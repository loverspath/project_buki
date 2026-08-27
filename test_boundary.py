import asyncio
import json
import os
import edge_tts

OUTPUT_DIR = r"C:\Users\rerun\opendcmart\projects\project_buki\scratch_tts_output"

async def inspect_boundaries():
    text = "흥! 뭐야...? 바~보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋... 허~접♡"
    comm = edge_tts.Communicate(text, "ko-KR-SunHiNeural", pitch="+42Hz", rate="+25%", boundary="WordBoundary")
    
    audio_path = os.path.join(OUTPUT_DIR, "inspect_boundary.mp3")
    meta_path = os.path.join(OUTPUT_DIR, "inspect_boundary.json")
    await comm.save(audio_path, meta_path)
    
    with open(meta_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            print(data)

if __name__ == "__main__":
    asyncio.run(inspect_boundaries())
