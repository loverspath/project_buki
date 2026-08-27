# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from .tts_service import synthesize_speech_base64 as synthesize_edge_tts
from .gpt_sovits_service import synthesize_gpt_sovits_base64, is_gpt_sovits_alive

# Load sample registry
SAMPLES_REGISTRY_PATH = Path(__file__).parent.parent.parent / "assets" / "voice_samples" / "sample_registry.json"
VOICE_SAMPLES: Dict[str, Any] = {}
if SAMPLES_REGISTRY_PATH.exists():
    try:
        with open(SAMPLES_REGISTRY_PATH, "r", encoding="utf-8") as f:
            VOICE_SAMPLES = json.load(f)
    except Exception as e:
        print(f"[TTS Manager] Could not load sample registry: {e}")

async def synthesize_smart_speech(
    text: str,
    persona_id: str,
    persona_config: Dict[str, Any],
    detected_actions: Optional[List[str]] = None,
    preferred_engine: str = "auto"
) -> Tuple[Optional[str], str]:
    """
    Intelligent multi-tier speech synthesis router:
    1. If GPT-SoVITS is preferred/auto and server is online -> Synthesizes zero-shot character acting audio.
    2. Selects emotion-appropriate 3-second reference wav based on detected actions.
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
        if detected_actions and "emotion_banks" in voice_sample_cfg:
            action_str = " ".join(detected_actions)
            banks = voice_sample_cfg["emotion_banks"]
            if any(k in action_str for k in ["비웃", "피식", "팔짱", "허접"]) and "smug" in banks:
                ref_wav = banks["smug"].get("ref_wav", ref_wav)
                prompt_text = banks["smug"].get("prompt_text", prompt_text)
            elif any(k in action_str for k in ["화남", "시끄", "바보"]) and "angry" in banks:
                ref_wav = banks["angry"].get("ref_wav", ref_wav)
                prompt_text = banks["angry"].get("prompt_text", prompt_text)

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

    # 2. Fallback to Edge-TTS
    voice = persona_config.get("voice", "ko-KR-SunHiNeural")
    pitch = persona_config.get("voice_pitch", "+0Hz")
    rate = persona_config.get("voice_rate", "+0%")

    audio_b64 = await synthesize_edge_tts(clean_text, voice, pitch, rate)
    if audio_b64:
        return audio_b64, "edge_tts"

    return None, "error"
