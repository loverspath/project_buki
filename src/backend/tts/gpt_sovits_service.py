# -*- coding: utf-8 -*-
import os
import time
import base64
from typing import Optional, Dict, Any
from pathlib import Path
import httpx

GPT_SOVITS_URL = os.getenv("GPT_SOVITS_URL", "http://127.0.0.1:9880")

_STATUS_CACHE = {"online": False, "timestamp": 0.0}
CACHE_TTL = 5.0 # Cache status for 5 seconds to avoid per-sentence TCP timeout

async def is_gpt_sovits_alive(force_refresh: bool = False) -> bool:
    """Checks if the local GPT-SoVITS API server is active with caching."""
    global _STATUS_CACHE
    now = time.time()
    if not force_refresh and (now - _STATUS_CACHE["timestamp"] < CACHE_TTL):
        return _STATUS_CACHE["online"]

    try:
        async with httpx.AsyncClient(timeout=0.8) as client:
            res = await client.get(f"{GPT_SOVITS_URL}/")
            is_alive = res.status_code in [200, 400, 405]
            _STATUS_CACHE = {"online": is_alive, "timestamp": now}
            return is_alive
    except Exception:
        _STATUS_CACHE = {"online": False, "timestamp": now}
        return False

async def synthesize_gpt_sovits_base64(
    text: str,
    ref_audio_path: str,
    prompt_text: str,
    prompt_lang: str = "ko",
    target_lang: str = "ko",
    speed: float = 1.0
) -> Optional[str]:
    """
    Calls local GPT-SoVITS API with zero-shot reference audio and prompt text.
    Returns base64 encoded audio string (WAV/MP3).
    """
    clean_text = text.strip()
    if not clean_text:
        return None

    if not os.path.isabs(ref_audio_path):
        base_dir = Path(__file__).parent.parent.parent
        ref_audio_path = str(base_dir / ref_audio_path)

    payload = {
        "text": clean_text,
        "text_lang": target_lang,
        "ref_audio_path": ref_audio_path,
        "prompt_text": prompt_text,
        "prompt_lang": prompt_lang,
        "top_k": 5,
        "top_p": 1.0,
        "temperature": 1.0,
        "speed": speed
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(f"{GPT_SOVITS_URL}/tts", json=payload)
            if res.status_code != 200:
                res = await client.post(f"{GPT_SOVITS_URL}/", json=payload)

            if res.status_code == 200 and res.content:
                return base64.b64encode(res.content).decode("utf-8")
            else:
                return None
    except Exception as e:
        print(f"[GPT-SoVITS Error] {e}")
        return None
