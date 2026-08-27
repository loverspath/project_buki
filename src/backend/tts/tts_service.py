# -*- coding: utf-8 -*-
import io
import re
import base64
import edge_tts
from typing import Optional

def enhance_prosody_for_character(text: str, tone: str = "mesugaki_sassy") -> str:
    """Enhances punctuation and intonation for more expressive character speech."""
    t = text.strip()
    if not t:
        return t

    if tone == "mesugaki_sassy":
        # Replace heart symbols and emojis with teasing elongations
        t = re.sub(r'[♡♥]', '~', t)
        # Add micro-pauses after iconic sassy interjections
        t = re.sub(r'^(흥|풋|하아\?|어라~|바보야|허접)([,~!\s]*)', r'\1... ', t)
        # Ensure question endings have distinct intonation
        t = re.sub(r'(잖아|거든|냐고|거야)\?', r'\1?!', t)
        # Normalize excessive punctuation
        t = re.sub(r'\.{3,}', '... ', t)
        t = re.sub(r'~{2,}', '~ ', t)
    elif tone == "cheerful_bright":
        t = re.sub(r'[♡♥]', '!', t)
        t = re.sub(r'~+', '!', t)
    
    return t.strip()

async def synthesize_speech_base64(
    text: str,
    voice: str = "ko-KR-SunHiNeural",
    pitch: str = "+0Hz",
    rate: str = "+0%",
    volume: str = "+0%",
    tone: str = "mesugaki_sassy"
) -> Optional[str]:
    """Synthesizes character-tuned text into MP3 using Edge-TTS and returns base64 string."""
    clean_text = enhance_prosody_for_character(text, tone)
    if not clean_text:
        return None

    try:
        communicate = edge_tts.Communicate(
            clean_text,
            voice,
            pitch=pitch,
            rate=rate,
            volume=volume
        )
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        
        audio_bytes = audio_stream.getvalue()
        if not audio_bytes:
            return None
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"[Edge-TTS Error] {e}")
        return None