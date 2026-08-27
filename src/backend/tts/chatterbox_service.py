# -*- coding: utf-8 -*-
import os
import json
import time
import httpx
import re
from pathlib import Path
from typing import Optional, List, Tuple

CHATTERBOX_URL = os.getenv("CHATTERBOX_URL", "http://127.0.0.1:9882")

_chatterbox_status_cache = {"alive": False, "last_check": 0.0}

def analyze_emotion_and_format_text(text: str, actions: List[str]) -> Tuple[str, str, float]:
    """
    Analyzes character action cues and voice nuances (including panting, breathiness, 
    sensual cues, teasing, whispering, etc.) and formats text with appropriate 
    paralinguistic cues and exaggeration weights.
    """
    action_str = " ".join(actions).lower()
    combined_context = f"{action_str} {text.lower()}"
    
    inferred_emotion = "default"
    exaggeration = 0.65
    processed_text = text

    # 1. Sensual / Moan / Erotic / Heated tone
    if any(k in combined_context for k in [
        "신음", "달아오른", "야릇", "흐트러", "앙탈", "달콤한 교성", "허덕이", "교태", "녹아내리", "신음소리", "애원"
    ]):
        inferred_emotion = "sensual"
        exaggeration = 0.95
        if not any(b in processed_text for b in ["하아", "응...", "읏...", "흐읏"]):
            processed_text = f"...읏, {processed_text}"

    # 2. Panting / Heavy Breathing / ASMR Breathiness
    elif any(k in combined_context for k in [
        "헐떡", "가쁜 숨", "거친 숨", "숨을 몰아쉬", "하악", "하아하아", "숨이 차", "가슴이 오르내리"
    ]):
        inferred_emotion = "panting"
        exaggeration = 0.90
        if not processed_text.startswith("...하아"):
            processed_text = f"...하아, 하아... {processed_text}"

    # 3. Flustered / Blushing / Embarrassed
    elif any(k in combined_context for k in [
        "얼굴을 붉히", "부끄러", "발개진", "부끄러워", "당황하", "허둥지둥", "더듬거리"
    ]):
        inferred_emotion = "flustered"
        exaggeration = 0.85
        if not any(k in processed_text for k in ["...!", "앗", "바,"]):
            processed_text = f"...앗, {processed_text}"

    # 4. Whispering / Ear-tickling / ASMR Soft
    elif any(k in combined_context for k in [
        "속삭", "귓가", "소곤", "귓속말", "살며시 다가와", "귀에 대고"
    ]):
        inferred_emotion = "whisper"
        exaggeration = 0.70
        processed_text = f"[whisper] {processed_text}"

    # 5. Smug / Mesugaki Teasing / Sassy Chuckle
    elif any(k in combined_context for k in [
        "비웃", "풋", "피식", "쿠후후", "우후후", "큭큭", "킥킥", "허접", "바보 오빠", "한심"
    ]):
        inferred_emotion = "smug"
        exaggeration = 0.88
        processed_text = f"[chuckle] {processed_text}"

    # 6. Laugh / Giggle
    elif any(k in combined_context for k in ["웃", "깔깔", "하하", "아하하"]):
        inferred_emotion = "laugh"
        exaggeration = 0.80
        processed_text = f"[laugh] {processed_text}"

    # 7. Sigh / Tired
    elif any(k in combined_context for k in ["한숨", "하아", "하휴", "휴", "귀찮"]):
        inferred_emotion = "sigh"
        exaggeration = 0.75
        processed_text = f"[sigh] {processed_text}"

    return processed_text, inferred_emotion, exaggeration

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

    # Analyze emotion, panting, breathiness, and tag text
    processed_text, inferred_emotion, exaggeration = analyze_emotion_and_format_text(
        text, detected_actions or []
    )

    final_emotion = override_emotion or inferred_emotion

    payload = {
        "text": processed_text,
        "ref_audio_path": ref_audio_path,
        "emotion": final_emotion,
        "language": prompt_lang,
        "exaggeration": exaggeration,
        "temperature": 0.85 if final_emotion in ["sensual", "panting", "angry"] else 0.80
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
