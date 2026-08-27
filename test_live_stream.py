# -*- coding: utf-8 -*-
import urllib.request
import json
import time

payload = {
    "message": "오빠 방 청소 다 했는데 칭찬해줘!",
    "persona_id": "mesugaki",
    "tts_engine": "gpt_sovits",
    "voice_enabled": True
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/chat/stream",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("Starting live chat stream test with Ollama & GPT-SoVITS...")
t0 = time.time()
with urllib.request.urlopen(req, timeout=40) as res:
    for line in res:
        line_str = line.decode("utf-8").strip()
        if line_str.startswith("data: "):
            try:
                data = json.loads(line_str[6:])
                evt_type = data.get("type")
                if evt_type == "token":
                    print(data.get("token", ""), end="", flush=True)
                elif evt_type == "audio":
                    print(f"\n[VOICE SYNTHESIZED] Dialogue: \"{data.get('spoken_text')}\" (Actions: {data.get('actions')})")
                elif evt_type == "action_cue":
                    print(f"\n[ACTION CUE (NO VOICE)] Actions: {data.get('actions')}")
                elif evt_type == "done":
                    print(f"\n[DONE in {time.time()-t0:.2f}s]")
            except Exception:
                pass
