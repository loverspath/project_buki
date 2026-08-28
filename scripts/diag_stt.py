# -*- coding: utf-8 -*-
import os
import glob
import json
import base64
import httpx
from dotenv import load_dotenv

load_dotenv("C:/Users/rerun/opendcmart/projects/project_buki/.env")
key = os.getenv("GEMINI_API_KEY")
clips = sorted(glob.glob("C:/Users/rerun/opendcmart/projects/project_buki/scratch_voice_extract/raw_candidate_clips/*.wav"))[1:11]

prompt = """You are an expert audio quality analyzer for VTuber voice cloning.
Analyze this Korean speech clip of Tenko Shibuki.
Transcribe spoken words verbatim in Korean.
Classify emotion: ['neutral', 'smug', 'tease', 'angry', 'whisper', 'sensual', 'flustered', 'resigned'].
Detect:
- has_donation_sound: boolean (donation chime/alert/bell/fanfare/TTS)
- has_rustling_or_bumps: boolean (plastic bag rustle, mic bump)
- is_clean: boolean (clean speech without donation alerts or heavy distortion)
Output JSON:
{"transcript": "...", "emotion": "...", "has_donation_sound": false, "has_rustling_or_bumps": false, "is_clean": true, "confidence": 0.95}
"""

for c in clips:
    with open(c, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": "audio/wav", "data": b64}}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
    }
    r = httpx.post(url, json=payload, timeout=20.0)
    print(f"Clip {os.path.basename(c)} (Status {r.status_code}):")
    if r.status_code == 200:
        print(" ", r.json()["candidates"][0]["content"]["parts"][0]["text"])
    else:
        print("  Error:", r.text[:200])
