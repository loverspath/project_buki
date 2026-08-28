# -*- coding: utf-8 -*-
import os
import json
import re
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path

from tts.tts_service import synthesize_speech_base64
from tts.gpt_sovits_service import synthesize_gpt_sovits_base64, is_gpt_sovits_alive
from tts.chatterbox_service import synthesize_speech_chatterbox, is_chatterbox_alive
from tts.index_tts_service import synthesize_index_tts_base64, is_index_tts_alive

SAMPLES_REGISTRY_PATH = Path(__file__).parent.parent.parent / "assets" / "voice_samples" / "sample_registry.json"

VOICE_SAMPLES: Dict[str, Any] = {}
if SAMPLES_REGISTRY_PATH.exists():
    try:
        with open(SAMPLES_REGISTRY_PATH, "r", encoding="utf-8-sig") as f:
            VOICE_SAMPLES = json.load(f)
    except Exception as e:
        print(f"[TTS Manager] Could not load sample registry: {e}")

def infer_emotion_from_context(combined_context: str) -> Optional[str]:
    """Infers the target acting emotion based on context and action keywords."""
    ctx = combined_context.lower()
    # NSFW / Sensual / Moan
    if any(k in ctx for k in [
        "신음", "달아오른", "야릇", "흐트러", "앙탈", "달콤한 교성", "허덕이", "교태", "녹아내리", "애원"
    ]):
        return "sensual"
    # Panting / Heavy Breathing
    elif any(k in ctx for k in [
        "헐떡", "가쁜 숨", "거친 숨", "숨을 몰아쉬", "하악", "하아하아", "숨이 차"
    ]):
        return "panting"
    # Flustered / Blushing
    elif any(k in ctx for k in [
        "얼굴을 붉히", "부끄러", "발개진", "부끄러워", "당황하", "허둥지둥", "홍조"
    ]):
        return "flustered"
    # Whispering / Intimate
    elif any(k in ctx for k in [
        "속삭", "귓가", "소곤", "귓속말", "살며시 다가와", "귀에 대고"
    ]):
        return "whisper"
    # Smug / Teasing
    elif any(k in ctx for k in [
        "비웃", "피식", "혀를 차", "한심", "콧방귀", "멍청", "허접", "풋", "깔보"
    ]):
        return "smug"
    # Playful / Tease
    elif any(k in ctx for k in [
        "놀리", "장난", "우후후", "쿠후후", "킥킥", "쿡쿡"
    ]):
        return "tease"
    # Terrified / Panic / Fear
    elif any(k in ctx for k in [
        "공포", "비명", "겁에 질", "사시나무", "떨며", "살려", "무서", "히익", "경악", "벌벌"
    ]):
        return "terrified"
    # Resigned / Low & Slow / Despair
    elif any(k in ctx for k in [
        "체념", "낮은 목소리", "느린 목소리", "한숨", "절망", "무기력", "멍하니", "지친", "포기"
    ]):
        return "resigned"
    # Crying / Weeping
    elif any(k in ctx for k in [
        "울먹", "눈물", "흐느끼", "훌쩍", "흑흑"
    ]):
        return "crying"
    # Angry / Screaming
    elif any(k in ctx for k in [
        "화", "버럭", "소리치", "짜증", "인상", "노려보", "째려", "가만 안"
    ]):
        return "angry"
    return None

def enrich_gpt_sovits_text(text: str, emotion: str) -> Tuple[str, float]:
    """
    Applies phoneme & punctuation styling for GPT-SoVITS autoregressive prosody:
    - Normalizes punctuation to prevent empty chunk token hallucination
    - Inserts clean vocalizations and adjusts synthesis speed
    """
    clean = re.sub(r"^[\s.,~…·!?;:]+", "", text).strip()
    clean = re.sub(r"[~]+$", ".", clean) # Replace trailing tildes with period to prevent Japanese long-vowel pitch drag
    clean = re.sub(r"[.]{2,}", ".", clean) # Normalize ellipsis to prevent AR token stalling
    clean = re.sub(r"[,]{2,}", ",", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    if not clean:
        return text, 1.0

    styled_text = clean
    speed = 1.0

    if emotion == "sensual":
        speed = 0.98 # Natural relaxed cadence without unnatural formant stretching
        if not any(b in styled_text for b in ["읏", "하아", "응"]):
            styled_text = f"읏, {styled_text}"
    elif emotion == "panting":
        speed = 1.06 # Rapid, breathless cadence
        if not styled_text.startswith("하아"):
            styled_text = f"하아, 하아, {styled_text}"
    elif emotion == "whisper":
        speed = 0.98 # Soft, intimate, gentle cadence
    elif emotion == "flustered":
        speed = 1.08 # Stuttering, agitated cadence
        if not any(k in styled_text for k in ["앗", "바,"]):
            styled_text = f"앗, {styled_text}!"
    elif emotion == "terrified":
        speed = 1.15 # High pitch, shivering, panicked gasp
        if not any(k in styled_text for k in ["히익", "으악", "꺅"]):
            styled_text = f"히익, {styled_text}!"
    elif emotion == "resigned":
        speed = 0.94 # Calm, low pitch, deep depressed sigh without dragging
        if not styled_text.startswith("하아"):
            styled_text = f"하아, {styled_text}"
    elif emotion == "crying":
        speed = 0.98 # Weeping, sobbing cadence
        if not any(k in styled_text for k in ["흑", "훌쩍"]):
            styled_text = f"흑... {styled_text}"
    elif emotion == "angry":
        speed = 1.12 # Fast, forceful, loud
    elif emotion in ["smug", "tease"]:
        speed = 1.02 # Crisp, sassy, relaxed

    return styled_text, speed

async def synthesize_smart_speech(
    text: str,
    persona_id: str,
    persona_config: Dict[str, Any],
    detected_actions: Optional[List[str]] = None,
    preferred_engine: str = "gpt_sovits",
    override_emotion: Optional[str] = None,
    target_duration_sec: Optional[float] = None
) -> Tuple[Optional[str], str]:
    """
    Intelligent speech synthesis router:
    - 'index_tts_2' / 'index_tts': IndexTTS-2 with 8D emotion vector, duration control, and zero-shot cloning.
    - 'gpt_sovits': GPT-SoVITS zero-shot synthesis with emotion banks & prosody enrichment.
    - 'chatterbox': 0.5B Chatterbox TTS with paralinguistic tag conversion ([laugh], [sigh], [whisper]).
    - 'auto': IndexTTS-2 ➔ GPT-SoVITS ➔ Chatterbox ➔ Edge-TTS.
    - 'edge_tts': Directly uses Edge-TTS.
    """
    clean_text = text.strip()
    if not clean_text:
        return None, "none"

    voice_sample_cfg = VOICE_SAMPLES.get(persona_id) or VOICE_SAMPLES.get("shibuki") or VOICE_SAMPLES.get("mesugaki", {})

    action_str = " ".join(detected_actions or []).lower()
    combined_context = f"{action_str} {clean_text.lower()}"
    target_emotion = override_emotion or infer_emotion_from_context(combined_context)

    # 1. IndexTTS-2 Engine (When selected or in auto mode)
    if preferred_engine in ["index_tts_2", "index_tts", "auto"]:
        ref_wav = voice_sample_cfg.get("default_ref_wav")
        prompt_text = voice_sample_cfg.get("default_prompt_text", "")
        prompt_lang = voice_sample_cfg.get("prompt_lang", "ko")
        target_lang = voice_sample_cfg.get("target_lang", "ko")

        if ref_wav:
            audio_b64 = await synthesize_index_tts_base64(
                text=clean_text,
                ref_audio_path=ref_wav,
                prompt_text=prompt_text,
                prompt_lang=prompt_lang,
                target_lang=target_lang,
                acting_emotion=target_emotion or "neutral",
                target_duration_sec=target_duration_sec,
                max_retries=1
            )
            if audio_b64:
                return audio_b64, "index_tts_2"

        if preferred_engine in ["index_tts_2", "index_tts"]:
            print(f"[TTS Manager] IndexTTS-2 (Port 9884) is offline/unavailable. Gracefully falling back to GPT-SoVITS/Edge-TTS...")

    # 2. Chatterbox Engine (When explicitly selected)
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

    # 3. GPT-SoVITS Execution (Priority & Strict mode / IndexTTS fallback)
    if preferred_engine in ["gpt_sovits", "auto", "index_tts_2", "index_tts"]:
        ref_wav = voice_sample_cfg.get("default_ref_wav")
        prompt_text = voice_sample_cfg.get("default_prompt_text", "")
        prompt_lang = voice_sample_cfg.get("prompt_lang", "ko")
        target_lang = voice_sample_cfg.get("target_lang", "ko")

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
                persona_id=persona_id,
                max_retries=2
            )
            if audio_b64:
                return audio_b64, "gpt_sovits"

        # If user strictly selected 'gpt_sovits', do not fall back to Edge-TTS
        if preferred_engine == "gpt_sovits":
            print(f"[TTS Manager] GPT-SoVITS requested strictly. Skipping fallback.")
            return None, "gpt_sovits_failed"

    # 4. Edge-TTS (When auto fallback or explicit edge_tts is selected)
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
