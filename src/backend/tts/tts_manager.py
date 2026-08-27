# -*- coding: utf-8 -*-
import os
import json
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path

from tts.tts_service import synthesize_speech_base64
from tts.gpt_sovits_service import synthesize_gpt_sovits_base64, is_gpt_sovits_alive

SAMPLES_REGISTRY_PATH = Path(__file__).parent.parent.parent / "assets" / "voice_samples" / "sample_registry.json"

VOICE_SAMPLES: Dict[str, Any] = {}
if SAMPLES_REGISTRY_PATH.exists():
    try:
        with open(SAMPLES_REGISTRY_PATH, "r", encoding="utf-8-sig") as f:
            VOICE_SAMPLES = json.load(f)
    except Exception as e:
        print(f"[TTS Manager] Could not load sample registry: {e}")

async def synthesize_smart_speech(
    text: str,
    persona_id: str,
    persona_config: Dict[str, Any],
    detected_actions: Optional[List[str]] = None,
    preferred_engine: str = "auto",
    override_emotion: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Intelligent multi-tier speech synthesis router:
    1. If GPT-SoVITS is preferred/auto and server is online -> Synthesizes zero-shot character acting audio.
    2. Selects emotion-appropriate reference wav based on detected actions or override_emotion.
    3. Seamlessly falls back to high-speed Edge-TTS if GPT-SoVITS is offline or fails.
    
    Returns: (audio_base64, engine_used)
    """
    clean_text = text.strip()
    if not clean_text:
        return None, "none"

    voice_sample_cfg = VOICE_SAMPLES.get(persona_id, {})
    gpt_sovits_online = await is_gpt_sovits_alive()

    # 1. Try GPT-SoVITS if requested or auto
    if (preferred_engine in ["gpt_sovits", "auto"]) and gpt_sovits_online and voice_sample_cfg:
        ref_wav = voice_sample_cfg.get("default_ref_wav")
        prompt_text = voice_sample_cfg.get("default_prompt_text", "")
        prompt_lang = voice_sample_cfg.get("prompt_lang", "ko")
        target_lang = voice_sample_cfg.get("target_lang", "ko")

        # Dynamic Emotion Bank Routing
        if "emotion_banks" in voice_sample_cfg:
            banks = voice_sample_cfg["emotion_banks"]
            target_emotion = override_emotion

            if not target_emotion and detected_actions:
                action_str = " ".join(detected_actions).lower()
                if any(k in action_str for k in ["비웃", "피식", "혀를 차", "한심", "콧방귀", "멍청", "허접", "풋"]):
                    target_emotion = "smug"
                elif any(k in action_str for k in ["놀리", "장난", "귓가", "속삭", "살살", "우후후", "쿠후후", "킥킥"]):
                    target_emotion = "tease"
                elif any(k in action_str for k in ["화", "버럭", "소리치", "짜증", "인상", "노려보", "째려"]):
                    target_emotion = "angry"
                elif any(k in action_str for k in ["얼굴을 붉", "부끄러", "더듬", "우물쭈물", "당황", "홍조"]):
                    target_emotion = "shy"

            if target_emotion and target_emotion in banks:
                ref_wav = banks[target_emotion].get("ref_wav", ref_wav)
                prompt_text = banks[target_emotion].get("prompt_text", prompt_text)
                prompt_lang = banks[target_emotion].get("lang", prompt_lang)
            elif target_emotion == "tease" and "smug" in banks:
                ref_wav = banks["smug"].get("ref_wav", ref_wav)
                prompt_text = banks["smug"].get("prompt_text", prompt_text)
                prompt_lang = banks["smug"].get("lang", prompt_lang)

        # Attempt GPT-SoVITS synthesis
        if ref_wav:
            audio_b64 = await synthesize_gpt_sovits_base64(
                text=clean_text,
                ref_audio_path=ref_wav,
                prompt_text=prompt_text,
                prompt_lang=prompt_lang,
                target_lang=target_lang
            )
            if audio_b64:
                return audio_b64, "gpt_sovits"

    # 2. Fallback to Edge-TTS with emotion prosody
    voice = persona_config.get("voice", "ko-KR-SunHiNeural")
    pitch = persona_config.get("voice_pitch", "+0Hz")
    rate = persona_config.get("voice_rate", "+0%")
    volume = persona_config.get("voice_volume", "+0%")
    tone = persona_config.get("voice_tone", "mesugaki_sassy")

    if override_emotion == "angry":
        pitch = "+30Hz"
        rate = "+26%"
    elif override_emotion in ["smug", "tease"]:
        pitch = "+42Hz"
        rate = "+20%"

    audio_b64 = await synthesize_speech_base64(
        text=clean_text,
        voice=voice,
        pitch=pitch,
        rate=rate,
        volume=volume,
        tone=tone
    )
    return audio_b64, "edge_tts"
