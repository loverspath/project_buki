# -*- coding: utf-8 -*-
"""
==============================================================================
Project BUKI - IndexTTS-2 Service Adapter
Supports:
  - Zero-Shot Voice Cloning with 3~8s Reference WAV
  - 8-Dimensional Emotion Vector Blending [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
  - Natural Language Soft Instruction (Prompt-guided emotion modulation)
  - Precision Duration Control (Audio-Visual LipSync & Dubbing Synchronization)
  - Native Multilingual Support (Korean 'ko', Japanese 'ja', Chinese 'zh', English 'en')
==============================================================================
"""

import os
import time
import base64
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import httpx

INDEX_TTS_URL = os.getenv("INDEX_TTS_URL", "http://127.0.0.1:9884")

_STATUS_CACHE = {"online": False, "timestamp": 0.0}
CACHE_TTL = 30.0  # 30-second status cache to avoid micro-polling during GPU inference

# 8D Emotion Vector Index: [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
EMOTION_VECTOR_PRESETS: Dict[str, Dict[str, Any]] = {
    "sensual": {
        "vector": [0.25, 0.00, 0.10, 0.00, 0.00, 0.35, 0.15, 0.60],
        "soft_instruction": "살짝 달아오른 나긋나긋하고 부끄러운 귓속말 톤과 호흡 감탄사",
        "speed": 0.90
    },
    "panting": {
        "vector": [0.10, 0.10, 0.00, 0.30, 0.00, 0.10, 0.40, 0.10],
        "soft_instruction": "가쁜 숨을 헐떡이며 몰아쉬는 거친 호흡 톤",
        "speed": 1.05
    },
    "terrified": {
        "vector": [0.00, 0.00, 0.20, 0.95, 0.10, 0.30, 0.85, 0.00],
        "soft_instruction": "공포에 질려 사시나무처럼 떨리는 비명과 울먹이는 호흡 톤",
        "speed": 1.16
    },
    "resigned": {
        "vector": [0.00, 0.00, 0.40, 0.00, 0.10, 0.95, 0.00, 0.40],
        "soft_instruction": "모든 것을 체념한 듯 낮고 느린 톤으로 깊은 한숨과 함께 무기력한 톤",
        "speed": 0.78
    },
    "crying": {
        "vector": [0.00, 0.00, 0.95, 0.20, 0.00, 0.70, 0.10, 0.00],
        "soft_instruction": "눈물을 글썽이며 서럽게 울먹이고 흐느끼는 톤",
        "speed": 0.95
    },
    "whisper": {
        "vector": [0.20, 0.00, 0.00, 0.00, 0.00, 0.10, 0.05, 0.90],
        "soft_instruction": "귓가에 조용히 밀착하여 나긋나긋하게 속삭이는 ASMR 톤",
        "speed": 0.92
    },
    "flustered": {
        "vector": [0.30, 0.20, 0.00, 0.30, 0.00, 0.00, 0.75, 0.10],
        "soft_instruction": "얼굴이 새빨개져서 당황하고 더듬거리며 앙탈부리는 톤",
        "speed": 1.08
    },
    "smug": {
        "vector": [0.85, 0.15, 0.00, 0.00, 0.20, 0.00, 0.10, 0.30],
        "soft_instruction": "비웃음과 함께 상대를 깔보고 짓궂게 놀리는 메스가키 톤",
        "speed": 1.00
    },
    "tease": {
        "vector": [0.80, 0.10, 0.00, 0.00, 0.05, 0.00, 0.20, 0.40],
        "soft_instruction": "장난기 넘치고 우후후 웃으며 상대를 도발하는 톤",
        "speed": 1.02
    },
    "angry": {
        "vector": [0.00, 0.95, 0.10, 0.00, 0.40, 0.00, 0.30, 0.00],
        "soft_instruction": "극도로 화가 나서 앙칼지게 쏘아붙이는 강한 어택 톤",
        "speed": 1.12
    },
    "neutral": {
        "vector": [0.20, 0.00, 0.00, 0.00, 0.00, 0.00, 0.05, 0.85],
        "soft_instruction": "자연스럽고 편안한 일상 대화 톤",
        "speed": 1.00
    }
}


async def is_index_tts_alive(force_refresh: bool = False) -> bool:
    """Checks if the local IndexTTS-2 API server / microservice is active."""
    global _STATUS_CACHE
    now = time.time()
    if not force_refresh and (now - _STATUS_CACHE["timestamp"] < CACHE_TTL) and _STATUS_CACHE["online"]:
        return True

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(f"{INDEX_TTS_URL}/health")
            is_alive = res.status_code in [200, 404, 405]
            _STATUS_CACHE = {"online": is_alive, "timestamp": now}
            return is_alive
    except Exception:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{INDEX_TTS_URL}/")
                is_alive = res.status_code in [200, 400, 404, 405]
                _STATUS_CACHE = {"online": is_alive, "timestamp": now}
                return is_alive
        except Exception:
            if (now - _STATUS_CACHE["timestamp"] < 60.0) and _STATUS_CACHE["online"]:
                return True
            _STATUS_CACHE = {"online": False, "timestamp": now}
            return False


async def synthesize_index_tts_base64(
    text: str,
    ref_audio_path: str,
    prompt_text: str = "",
    prompt_lang: str = "ko",
    target_lang: str = "ko",
    acting_emotion: str = "neutral",
    target_duration_sec: Optional[float] = None,
    speed: Optional[float] = None,
    max_retries: int = 2
) -> Optional[str]:
    """
    Calls local IndexTTS-2 API with zero-shot reference audio, 8D emotion vector,
    and optional precise duration control.
    """
    clean_text = text.strip()
    if not clean_text:
        return None

    if not os.path.isabs(ref_audio_path):
        base_dir = Path(__file__).parent.parent.parent
        ref_audio_path = str(base_dir / ref_audio_path)

    ref_audio_path = ref_audio_path.replace("\\", "/")

    # Retrieve Emotion Vector and Soft Instruction Preset
    emo_preset = EMOTION_VECTOR_PRESETS.get(acting_emotion, EMOTION_VECTOR_PRESETS["neutral"])
    emotion_vector = emo_preset["vector"]
    soft_instruction = emo_preset["soft_instruction"]
    speed_factor = speed if speed is not None else emo_preset["speed"]

    payload: Dict[str, Any] = {
        "text": clean_text,
        "text_lang": target_lang,
        "ref_audio_path": ref_audio_path,
        "prompt_text": prompt_text,
        "prompt_lang": prompt_lang,
        "emotion_vector": emotion_vector,
        "soft_instruction": soft_instruction,
        "speed_factor": speed_factor,
        "media_type": "wav"
    }

    # If duration is explicitly specified for lipsync/dubbing synchronization
    if target_duration_sec is not None and target_duration_sec > 0.0:
        payload["duration_sec"] = round(target_duration_sec, 2)
        payload["duration_control"] = True

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(f"{INDEX_TTS_URL}/tts", json=payload)
                if res.status_code == 200 and res.content:
                    _STATUS_CACHE["online"] = True
                    _STATUS_CACHE["timestamp"] = time.time()
                    return base64.b64encode(res.content).decode("utf-8")
                else:
                    print(f"[IndexTTS-2 Non-200] Attempt {attempt+1}/{max_retries+1}: Status {res.status_code}, Body: {res.text[:200]}")
        except httpx.TimeoutException:
            print(f"[IndexTTS-2 Timeout] Attempt {attempt+1}/{max_retries+1}: GPU inference took longer than expected, retrying...")
            await asyncio.sleep(1.0)
        except Exception as e:
            print(f"[IndexTTS-2 Connection Error] Attempt {attempt+1}/{max_retries+1}: {e}")
            await asyncio.sleep(1.0)

    return None
