# -*- coding: utf-8 -*-
import os
import time
import base64
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import httpx

GPT_SOVITS_URL = os.getenv("GPT_SOVITS_URL", "http://127.0.0.1:9880")

_STATUS_CACHE = {"online": False, "timestamp": 0.0}
CACHE_TTL = 30.0 # Cache status for 30 seconds to prevent healthcheck collisions during GPU compute

_CURRENT_PERSONA = None
_MODEL_CONFIGS = {
    "shibuki": {
        "sovits": r"C:/Users/rerun/opendcmart/tools/GPT-SoVITS/SoVITS_weights_v2/shibuki_e12_s600.pth",
        "gpt": r"C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_weights_v2/shibuki-e15.ckpt"
    },
    "mutsuki": {
        "sovits": r"C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth",
        "gpt": r"C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt"
    },
    "mesugaki": {
        "sovits": r"C:/Users/rerun/opendcmart/tools/GPT-SoVITS/SoVITS_weights_v2/shibuki_e12_s600.pth",
        "gpt": r"C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_weights_v2/shibuki-e15.ckpt"
    }
}

async def ensure_persona_weights(persona_id: str = "shibuki") -> bool:
    """Dynamically loads fine-tuned or base GPT/SoVITS weights for the active persona."""
    global _CURRENT_PERSONA
    target_key = persona_id if persona_id in _MODEL_CONFIGS else "shibuki"
    if _CURRENT_PERSONA == target_key:
        return True

    cfg = _MODEL_CONFIGS.get(target_key)
    if not cfg:
        return True

    sovits_file = Path(cfg["sovits"])
    gpt_file = Path(cfg["gpt"])

    if not sovits_file.exists() or not gpt_file.exists():
        print(f"[GPT-SoVITS] Custom weights for '{target_key}' not found, keeping active models.")
        return True

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res_s = await client.get(f"{GPT_SOVITS_URL}/set_sovits_weights", params={"weights_path": str(sovits_file)})
            res_g = await client.get(f"{GPT_SOVITS_URL}/set_gpt_weights", params={"weights_path": str(gpt_file)})
            if res_s.status_code == 200 and res_g.status_code == 200:
                _CURRENT_PERSONA = target_key
                print(f"[GPT-SoVITS] Successfully loaded models for persona '{target_key}'")
                return True
    except Exception as e:
        print(f"[GPT-SoVITS] Failed to switch models to '{target_key}': {e}")
    return False

async def is_gpt_sovits_alive(force_refresh: bool = False) -> bool:
    """Checks if the local GPT-SoVITS API server is active with generous timeout."""
    global _STATUS_CACHE
    now = time.time()
    if not force_refresh and (now - _STATUS_CACHE["timestamp"] < CACHE_TTL) and _STATUS_CACHE["online"]:
        return True

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(f"{GPT_SOVITS_URL}/")
            is_alive = res.status_code in [200, 400, 404, 405]
            _STATUS_CACHE = {"online": is_alive, "timestamp": now}
            return is_alive
    except Exception:
        # If cached as online recently, don't hastily declare offline during active GPU generation
        if (now - _STATUS_CACHE["timestamp"] < 60.0) and _STATUS_CACHE["online"]:
            return True
        _STATUS_CACHE = {"online": False, "timestamp": now}
        return False

async def synthesize_gpt_sovits_base64(
    text: str,
    ref_audio_path: str,
    prompt_text: str,
    prompt_lang: str = "ko",
    target_lang: str = "ko",
    speed: float = 1.0,
    persona_id: str = "shibuki",
    max_retries: int = 2
) -> Optional[str]:
    """
    Calls local GPT-SoVITS api_v2 with zero-shot reference audio and prompt text.
    Automatically ensures appropriate fine-tuned weights are active.
    """
    clean_text = text.strip()
    if not clean_text:
        return None

    await ensure_persona_weights(persona_id)

    if not os.path.isabs(ref_audio_path):
        base_dir = Path(__file__).parent.parent.parent
        ref_audio_path = str(base_dir / ref_audio_path)

    # Normalize backslashes for Windows path compatibility
    ref_audio_path = ref_audio_path.replace("\\", "/")

    # Normalize Korean language codes to all_ko for strict Korean phonemizer
    eff_target_lang = "all_ko" if target_lang in ["ko", "all_ko", "korean", "KO", "KOR"] else target_lang
    eff_prompt_lang = "all_ko" if prompt_lang in ["ko", "all_ko", "korean", "KO", "KOR"] else prompt_lang

    payload = {
        "text": clean_text,
        "text_lang": eff_target_lang,
        "ref_audio_path": ref_audio_path,
        "prompt_text": prompt_text,
        "prompt_lang": eff_prompt_lang,
        "top_k": 10,
        "top_p": 0.80,
        "temperature": 0.65,
        "speed_factor": speed,
        "text_split_method": "cut5",
        "batch_size": 1,
        "media_type": "wav",
        "streaming_mode": False
    }

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(f"{GPT_SOVITS_URL}/tts", json=payload)
                if res.status_code == 200 and res.content:
                    _STATUS_CACHE["online"] = True
                    _STATUS_CACHE["timestamp"] = time.time()
                    return base64.b64encode(res.content).decode("utf-8")
                else:
                    print(f"[GPT-SoVITS Non-200] Attempt {attempt+1}/{max_retries+1}: Status {res.status_code}, Body: {res.text[:200]}")
        except httpx.TimeoutException:
            print(f"[GPT-SoVITS Timeout] Attempt {attempt+1}/{max_retries+1}: GPU inference took longer than expected, retrying...")
            await asyncio.sleep(1.0)
        except Exception as e:
            print(f"[GPT-SoVITS Connection Error] Attempt {attempt+1}/{max_retries+1}: {e}")
            await asyncio.sleep(1.0)

    return None
