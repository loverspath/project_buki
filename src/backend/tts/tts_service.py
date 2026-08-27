# -*- coding: utf-8 -*-
import io
import base64
import edge_tts
from typing import Optional

async def synthesize_speech_base64(
    text: str,
    voice: str = "ko-KR-SunHiNeural",
    pitch: str = "+0Hz",
    rate: str = "+0%"
) -> Optional[str]:
    """Synthesizes text into MP3 using Edge-TTS and returns base64 string."""
    clean_text = text.strip()
    if not clean_text:
        return None
    try:
        communicate = edge_tts.Communicate(clean_text, voice, pitch=pitch, rate=rate)
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        
        audio_bytes = audio_stream.getvalue()
        if not audio_bytes:
            return None
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"[TTS Error] {e}")
        return None