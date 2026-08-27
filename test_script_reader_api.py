# -*- coding: utf-8 -*-
import urllib.request
import json
import time

script_text = """(방 문을 열고 혀를 차며 어이없다는 듯이 팔짱을 낀다.)
"뭐야, 바보 오빠? 아직도 자고 있는 거야? 풋, 진짜 못말리는 허접이네~"
그녀는 콧방귀를 뀌며 버럭 소리쳤다.
"당장 안 일어나면 진짜 폭탄 설치해버릴 테니까 각오해, 바보야!"
그러고는 귓가에 살며시 다가와 짓궂게 속삭였다.
"자꾸 늦장 부리면... 무슨 일이 일어날지 몰라? 우후후~"
"""

parse_payload = {
    "script_text": script_text,
    "persona_id": "mesugaki"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/script/parse",
    data=json.dumps(parse_payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("Testing /api/script/parse...")
with urllib.request.urlopen(req, timeout=10) as res:
    data = json.loads(res.read())
    print(f"Total Dialogues: {data.get('total_dialogues')}")
    print("=== Parsed Segments ===")
    for s in data["segments"]:
        print(f"Type: {s['type']} | Emotion: {s['inferred_emotion']} | Text: {s['text'][:50]}")

dialogues = [s for s in data["segments"] if s["type"] == "dialogue"]
print(f"\nTesting /api/script/tts_segment for {len(dialogues)} dialogues...")

for i, d in enumerate(dialogues):
    t0 = time.time()
    tts_payload = {
        "dialogue": d["spoken_text"],
        "persona_id": "mesugaki",
        "inferred_emotion": d["inferred_emotion"],
        "tts_engine": "gpt_sovits",
        "context_narration": d["context_narration"]
    }
    tts_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/script/tts_segment",
        data=json.dumps(tts_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(tts_req, timeout=20) as res:
        tts_data = json.loads(res.read())
        print(f"[{i+1}/{len(dialogues)}] Spoken: \"{d['spoken_text'][:20]}...\" | Emotion: {tts_data.get('inferred_emotion')} | Engine: {tts_data.get('engine_used')} | Length: {len(tts_data.get('audio_base64', ''))} chars in {time.time()-t0:.2f}s")
