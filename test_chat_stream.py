# -*- coding: utf-8 -*-
import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

payload = {
    "message": "(피곤한 표정으로 의자에 기대앉으며) 아... 오늘 진짜 힘들었다. 나 좀 칭찬해주면 안 돼?",
    "persona_id": "mesugaki",
    "model": "huihui_ai/qwen2.5-coder-abliterate:14b",
    "voice_enabled": True,
    "tts_engine": "gpt_sovits"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/chat/stream",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("Testing Live Chat Stream with Optimized Qwen 14B Mesugaki...")
with urllib.request.urlopen(req, timeout=60) as res:
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
                print(f"\n[🎙️ TTS Synthesized: '{spoken}' via {eng}]")

print("\nStream finished successfully!")
