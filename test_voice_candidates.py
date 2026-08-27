import asyncio
import os
import edge_tts

OUTPUT_DIR = r"C:\Users\rerun\opendcmart\projects\project_buki\scratch_tts_output"

async def test_voices_reading_korean():
    candidate_voices = [
        "ko-KR-SunHiNeural",
        "ko-KR-HyunsuMultilingualNeural",
        "en-US-AvaMultilingualNeural",
        "en-US-EmmaMultilingualNeural",
        "ja-JP-NanamiNeural",
        "ja-JP-KeitaNeural",
        "zh-CN-XiaoyiNeural",
    ]
    
    text = "흥! 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~"
    
    for voice in candidate_voices:
        out_path = os.path.join(OUTPUT_DIR, f"voice_{voice.replace(':', '_')}.mp3")
        try:
            comm = edge_tts.Communicate(text, voice, pitch="+40Hz", rate="+25%")
            await comm.save(out_path)
            print(f"[OK] Voice {voice}: size={os.path.getsize(out_path)}")
        except Exception as e:
            print(f"[FAIL] Voice {voice}: {e}")

if __name__ == "__main__":
    asyncio.run(test_voices_reading_korean())
