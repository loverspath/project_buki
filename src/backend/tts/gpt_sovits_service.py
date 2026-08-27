# -*- coding: utf-8 -*-
import os
import base64
from typing import Optional, Dict, Any
from pathlib import Path
import httpx

GPT_SOVITS_URL = os.getenv("GPT_SOVITS_URL", "http://127.0.0.1:9880")

async def is_gpt_sovits_alive() -> bool:
    """Checks if the local GPT-SoVITS API server is active and reachable."""
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            # GPT-SoVITS returns 200 or 400 on root/control endpoint
            res = await client.get(f"{GPT_SOVITS_URL}/")
            return res.status_code in [200, 400, 405]
    except Exception:
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

    # Resolve absolute path for reference wav
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Supports both /tts endpoint and root POST endpoint in GPT-SoVITS v2
            res = await client.post(f"{GPT_SOVITS_URL}/tts", json=payload)
            if res.status_code != 200:
                res = await client.post(f"{GPT_SOVITS_URL}/", json=payload)

            if res.status_code == 200 and res.content:
                return base64.b64encode(res.content).decode("utf-8")
            else:
                print(f"[GPT-SoVITS] HTTP {res.status_code}: {res.text[:100]}")
                return None
    except Exception as e:
        print(f"[GPT-SoVITS Error] {e}")
        return None
