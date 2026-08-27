# -*- coding: utf-8 -*-
import os
import json
import re
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path

from tts.tts_service import synthesize_speech_base64
from tts.gpt_sovits_service import synthesize_gpt_sovits_base64, is_gpt_sovits_alive
from tts.chatterbox_service import synthesize_speech_chatterbox, is_chatterbox_alive

SAMPLES_REGISTRY_PATH = Path(__file__).parent.parent.parent / "assets" / "voice_samples" / "sample_registry.json"

VOICE_SAMPLES: Dict[str, Any] = {}
if SAMPLES_REGISTRY_PATH.exists():
    try:
        with open(SAMPLES_REGISTRY_PATH, "r", encoding="utf-8-sig") as f:
            VOICE_SAMPLES = json.load(f)
    except Exception as e:
        print(f"[TTS Manager] Could not load sample registry: {e}")

def enrich_gpt_sovits_text(text: str, emotion: str) -> Tuple[str, float]:
    """
    Applies phoneme & punctuation styling for GPT-SoVITS autoregressive prosody:
    - Normalizes punctuation to prevent empty chunk token hallucination
    - Inserts clean vocalizations and adjusts synthesis speed
    """
    # Clean leading/trailing punctuation debris
    clean = re.sub(r"^[\s.,~…·!?;:]+", "", text).strip()
    clean = re.sub(r"[.]{2,}", "…", clean)
    clean = re.sub(r"[,]{2,}", ",", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    if not clean:
        return text, 1.0

    styled_text = clean
    speed = 1.0

    if emotion == "sensual":
        speed = 0.90 # Slower, breathier, more relaxed
        if not any(b in styled_text for b in ["읏", "하아", "응"]):
            styled_text = f"읏, {styled_text}~"
    elif emotion == "panting":
        speed = 1.05 # Rapid, breathless cadence
        if not styled_text.startswith("하아"):
            styled_text = f"하아, 하아, {styled_text}"
    elif emotion == "whisper":
        speed = 0.92 # Soft, intimate, gentle cadence
    elif emotion == "flustered":
        speed = 1.08 # Stuttering, agitated cadence
        if not any(k in styled_text for k in ["앗", "바,"]):
            styled_text = f"앗, {styled_text}!"
    elif emotion == "terrified":
        speed = 1.16 # High pitch, shivering, panicked gasp
        if not any(k in styled_text for k in ["히익", "으악", "꺅"]):
            styled_text = f"히익, {styled_text}!"
    elif emotion == "resigned":
        speed = 0.78 # Very slow, low pitch, deep depressed sigh
        if not styled_text.startswith("하아"):
            styled_text = f"하아... {styled_text}"
    elif emotion == "crying":
        speed = 0.95 # Weeping, sobbing cadence
        if not any(k in styled_text for k in ["흑", "훌쩍"]):
            styled_text = f"흑... {styled_text}"
    elif emotion == "angry":
        speed = 1.12 # Fast, forceful, loud
    elif emotion in ["smug", "tease"]:
        speed = 1.00 # Sassy, relaxed

    return styled_text, speed

async def synthesize_smart_speech(
    text: str,
    persona_id: str,
    persona_config: Dict[str, Any],
    detected_actions: Optional[List[str]] = None,
    preferred_engine: str = "gpt_sovits",
    override_emotion: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Intelligent speech synthesis router:
    - 'gpt_sovits': Patiently waits for GPT-SoVITS synthesis with dynamic emotion banks & prosody enrichment.
    - 'chatterbox': Uses 0.5B Chatterbox TTS with paralinguistic tag conversion ([laugh], [sigh], [whisper]).
    - 'auto': Tries GPT-SoVITS, then Chatterbox, then falls back to Edge-TTS.
    - 'edge_tts': Directly uses Edge-TTS.
    """
    clean_text = text.strip()
    if not clean_text:
        return None, "none"

    voice_sample_cfg = VOICE_SAMPLES.get(persona_id) or VOICE_SAMPLES.get("mesugaki", {})

    # 1. Chatterbox Engine (When explicitly selected)
    if preferred_engine == "chatterbox":
        audio_b64 = await synthesize_speech_chatterbox(
            text=clean_text,
            persona_id=persona_id,
            persona_config=persona_config,
            detected_actions=detected_actions,
            override_emotion=override_emotion
        )
        if audio_b64:
            return audio_b64, "chatterbox"
        print(f"[TTS Manager] Chatterbox synthesis failed or offline.")
        return None, "chatterbox_failed"

    # 2. GPT-SoVITS Execution (Priority & Strict mode)
    if preferred_engine in ["gpt_sovits", "auto"]:
        ref_wav = voice_sample_cfg.get("default_ref_wav")
        prompt_text = voice_sample_cfg.get("default_prompt_text", "")
        prompt_lang = voice_sample_cfg.get("prompt_lang", "ko")
        target_lang = voice_sample_cfg.get("target_lang", "ko")

        target_emotion = override_emotion
        action_str = " ".join(detected_actions or []).lower()
        combined_context = f"{action_str} {clean_text.lower()}"

        if not target_emotion:
            # NSFW / Sensual / Moan
            if any(k in combined_context for k in [
                "신음", "달아오른", "야릇", "흐트러", "앙탈", "달콤한 교성", "허덕이", "교태", "녹아내리", "애원"
            ]):
                target_emotion = "sensual"
            # Panting / Heavy Breathing
            elif any(k in combined_context for k in [
                "헐떡", "가쁜 숨", "거친 숨", "숨을 몰아쉬", "하악", "하아하아", "숨이 차"
            ]):
                target_emotion = "panting"
            # Flustered / Blushing
            elif any(k in combined_context for k in [
                "얼굴을 붉히", "부끄러", "발개진", "부끄러워", "당황하", "허둥지둥"
            ]):
                target_emotion = "flustered"
            # Whispering / Intimate
            elif any(k in combined_context for k in [
                "속삭", "귓가", "소곤", "귓속말", "살며시 다가와", "귀에 대고"
            ]):
                target_emotion = "whisper"
            # Smug / Teasing
            elif any(k in combined_context for k in [
                "비웃", "피식", "혀를 차", "한심", "콧방귀", "멍청", "허접", "풋"
            ]):
                target_emotion = "smug"
            # Playful / Tease
            elif any(k in combined_context for k in [
                "놀리", "장난", "우후후", "쿠후후", "킥킥"
            ]):
                target_emotion = "tease"
            # Terrified / Panic / Fear
            elif any(k in combined_context for k in [
                "공포", "비명", "겁에 질", "사시나무", "떨며", "살려", "무서", "히익", "경악", "벌벌"
            ]):
                target_emotion = "terrified"
            # Resigned / Low & Slow / Despair
            elif any(k in combined_context for k in [
                "체념", "낮은 목소리", "느린 목소리", "한숨", "절망", "무기력", "멍하니", "지친", "포기"
            ]):
                target_emotion = "resigned"
            # Crying / Weeping
            elif any(k in combined_context for k in [
                "울먹", "눈물", "흐느끼", "훌쩍", "흑흑"
            ]):
                target_emotion = "crying"
            # Angry / Screaming
            elif any(k in combined_context for k in [
                "화", "버럭", "소리치", "짜증", "인상", "노려보", "째려"
            ]):
                target_emotion = "angry"

        # Apply emotion bank ref wav if available
        if "emotion_banks" in voice_sample_cfg:
            banks = voice_sample_cfg["emotion_banks"]
            if target_emotion in banks:
                ref_wav = banks[target_emotion].get("ref_wav", ref_wav)
                prompt_text = banks[target_emotion].get("prompt_text", prompt_text)
                prompt_lang = banks[target_emotion].get("lang", prompt_lang)
            elif target_emotion in ["sensual", "whisper", "tease"] and "tease" in banks:
                ref_wav = banks["tease"].get("ref_wav", ref_wav)
                prompt_text = banks["tease"].get("prompt_text", prompt_text)
                prompt_lang = banks["tease"].get("lang", prompt_lang)
            elif target_emotion in ["terrified", "angry"] and "angry" in banks:
                ref_wav = banks["angry"].get("ref_wav", ref_wav)
                prompt_text = banks["angry"].get("prompt_text", prompt_text)
                prompt_lang = banks["angry"].get("lang", prompt_lang)

        # Prosody & text phoneme enrichment
        enriched_text, speed = enrich_gpt_sovits_text(clean_text, target_emotion or "default")

        if ref_wav:
            audio_b64 = await synthesize_gpt_sovits_base64(
                text=enriched_text,
                ref_audio_path=ref_wav,
                prompt_text=prompt_text,
                prompt_lang=prompt_lang,
                target_lang=target_lang,
                speed=speed,
                max_retries=2
            )
            if audio_b64:
                return audio_b64, "gpt_sovits"

        # If user strictly selected 'gpt_sovits', do not fall back to Edge-TTS
        if preferred_engine == "gpt_sovits":
            print(f"[TTS Manager] GPT-SoVITS requested strictly. Skipping fallback.")
            return None, "gpt_sovits_failed"

    # 3. Edge-TTS (When auto fallback or explicit edge_tts is selected)
    voice = persona_config.get("voice", "ko-KR-SunHiNeural")
    pitch = persona_config.get("voice_pitch", "+40Hz")
    rate = persona_config.get("voice_rate", "+22%")
    volume = persona_config.get("voice_volume", "+10%")
    tone = persona_config.get("voice_tone", "mesugaki_sassy")

    audio_b64 = await synthesize_speech_base64(
        text=clean_text,
        voice=voice,
        pitch=pitch,
        rate=rate,
        volume=volume,
        tone=tone
    )
    return audio_b64, "edge_tts"
