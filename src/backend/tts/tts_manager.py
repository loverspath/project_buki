# -*- coding: utf-8 -*-
import os
import json
import re
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
    preferred_engine: str = "gpt_sovits",
    override_emotion: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Intelligent speech synthesis router:
    - If preferred_engine == 'gpt_sovits': Patiently waits for GPU synthesis (up to 120s) without switching to Edge-TTS.
    - If preferred_engine == 'auto': Tries GPT-SoVITS first, falls back to Edge-TTS only if offline.
    - If preferred_engine == 'edge_tts': Directly uses Edge-TTS.
    """
    clean_text = text.strip()
    if not clean_text:
        return None, "none"

    voice_sample_cfg = VOICE_SAMPLES.get(persona_id) or VOICE_SAMPLES.get("mesugaki", {})

    # 1. GPT-SoVITS Execution (Priority & Strict mode)
    if preferred_engine in ["gpt_sovits", "auto"]:
        ref_wav = voice_sample_cfg.get("default_ref_wav")
        prompt_text = voice_sample_cfg.get("default_prompt_text", "")
        prompt_lang = voice_sample_cfg.get("prompt_lang", "ja")
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

            if target_emotion and target_emotion in banks:
                ref_wav = banks[target_emotion].get("ref_wav", ref_wav)
                prompt_text = banks[target_emotion].get("prompt_text", prompt_text)
                prompt_lang = banks[target_emotion].get("lang", prompt_lang)

        if ref_wav:
            audio_b64 = await synthesize_gpt_sovits_base64(
                text=clean_text,
                ref_audio_path=ref_wav,
                prompt_text=prompt_text,
                prompt_lang=prompt_lang,
                target_lang=target_lang,
                speed=1.0,
                max_retries=2
            )
            if audio_b64:
                return audio_b64, "gpt_sovits"

        # If user strictly selected 'gpt_sovits', do not fall back to Edge-TTS
        if preferred_engine == "gpt_sovits":
            print(f"[TTS Manager] GPT-SoVITS requested strictly. Skipping Edge-TTS fallback.")
            return None, "gpt_sovits_failed"

    # 2. Edge-TTS (When auto fallback or explicit edge_tts is selected)
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
