# -*- coding: utf-8 -*-
import urllib.request
import json
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

payload = {
    "message": "오빠 지금 코딩하다가 세그폴트 떴어... 나 좀 도와줘.",
    "persona_id": "mesugaki",
    "model": "nvidia/nemotron-3-ultra-550b-a55b",
    "voice_enabled": True,
    "tts_engine": "gpt_sovits"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/chat/stream",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("Testing Nemotron 3 Ultra 550B Live Streaming with Mesugaki Tone...")
t0 = time.time()
with urllib.request.urlopen(req, timeout=120) as res:
    for line in res:
        line_str = line.decode("utf-8").strip()
        if line_str.startswith("data: "):
            data = json.loads(line_str[6:])
            t = data.get("type")
            if t == "token":
                print(data.get("token"), end="", flush=True)
            elif t == "audio":
                spoken = data.get("spoken_text")
                eng = data.get("engine_used")
                print(f"\n[🎙️ TTS: '{spoken}' via {eng}]")

print(f"\n\nTurn completed in {time.time()-t0:.2f}s!")
