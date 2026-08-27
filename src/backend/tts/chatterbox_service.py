# -*- coding: utf-8 -*-
import os
import json
import time
import httpx
from pathlib import Path
from typing import Optional, List, Tuple

CHATTERBOX_URL = os.getenv("CHATTERBOX_URL", "http://127.0.0.1:9882")

_chatterbox_status_cache = {"alive": False, "last_check": 0.0}

def map_actions_to_chatterbox_tags(text: str, actions: List[str]) -> str:
    """
    Converts Korean action cues into Chatterbox paralinguistic tags:
    - [laugh], [chuckle], [sigh], [whisper], [cough]
    """
    tagged_text = text
    action_str = " ".join(actions).lower()

    prefix_tags = []
    if any(k in action_str or k in text for k in ["비웃", "풋", "피식", "쿠후후", "우후후", "큭큭", "킥킥"]):
        prefix_tags.append("[chuckle]")
    elif any(k in action_str or k in text for k in ["웃", "깔깔", "하하"]):
        prefix_tags.append("[laugh]")
        
    if any(k in action_str or k in text for k in ["한숨", "하아", "하휴", "휴"]):
        prefix_tags.append("[sigh]")
        
    if any(k in action_str or k in text for k in ["속삭", "소곤", "귓가"]):
        prefix_tags.append("[whisper]")

    if prefix_tags:
        tagged_text = f"{' '.join(prefix_tags)} {tagged_text}"

    return tagged_text

async def is_chatterbox_alive() -> bool:
    """Checks if Chatterbox microservice on port 9882 is responding."""
    now = time.time()
    if now - _chatterbox_status_cache["last_check"] < 5.0:
        return _chatterbox_status_cache["alive"]

    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            res = await client.get(f"{CHATTERBOX_URL}/health")
            alive = (res.status_code == 200)
            _chatterbox_status_cache["alive"] = alive
            _chatterbox_status_cache["last_check"] = now
            return alive
    except Exception:
        _chatterbox_status_cache["alive"] = False
        _chatterbox_status_cache["last_check"] = now
        return False

async def synthesize_speech_chatterbox(
    text: str,
    persona_id: str,
    persona_config: dict,
    detected_actions: Optional[List[str]] = None,
    override_emotion: Optional[str] = None
) -> Optional[str]:
    """
    Calls Chatterbox server on port 9882 with reference voice and paralinguistic emotion tags.
    """
    if not text.strip():
        return None

    # Reference sample lookup
    assets_dir = Path(__file__).parent.parent.parent / "assets" / "voice_samples"
    registry_path = assets_dir / "sample_registry.json"
    ref_audio_path = None
    prompt_lang = "ko"

    if registry_path.exists():
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                reg = json.load(f)
                p_data = reg.get(persona_id, reg.get("mesugaki", {}))
                sample_file = p_data.get("sample_file")
                prompt_lang = p_data.get("prompt_lang", "ko")
                if sample_file:
                    target_wav = assets_dir / sample_file
                    if target_wav.exists():
                        ref_audio_path = str(target_wav.resolve())
        except Exception as e:
            print(f"[Chatterbox Registry Warning] {e}")

    # Convert action cues to Chatterbox inline tags
    processed_text = map_actions_to_chatterbox_tags(text, detected_actions or [])

    payload = {
        "text": processed_text,
        "ref_audio_path": ref_audio_path,
        "emotion": override_emotion or "default",
        "language": prompt_lang
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(f"{CHATTERBOX_URL}/tts", json=payload)
            if res.status_code == 200:
                data = res.json()
                return data.get("audio_base64")
            else:
                print(f"[Chatterbox Error] HTTP {res.status_code}: {res.text[:120]}")
                return None
    except Exception as e:
        print(f"[Chatterbox Request Exception] {e}")
        return None
