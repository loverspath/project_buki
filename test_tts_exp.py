import asyncio
import os
import edge_tts

OUTPUT_DIR = r"C:\Users\rerun\opendcmart\projects\project_buki\scratch_tts_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

test_sentences = [
    "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~",
    "허접 오빠~ 이 정도로 지친 거야? 진짜 구제불능이네!",
    "하아? 내가 언제 오빠를 걱정했다고 그래? 착각하지 마, 바보야! 흥!",
]

async def test_voices_and_pitches():
    configs = [
        # SunHi Neural tests
        {"name": "sunhi_default", "voice": "ko-KR-SunHiNeural", "pitch": "+0Hz", "rate": "+0%"},
        {"name": "sunhi_p20_r15", "voice": "ko-KR-SunHiNeural", "pitch": "+20Hz", "rate": "+15%"},
        {"name": "sunhi_p35_r20", "voice": "ko-KR-SunHiNeural", "pitch": "+35Hz", "rate": "+20%"},
        {"name": "sunhi_p40_r25", "voice": "ko-KR-SunHiNeural", "pitch": "+40Hz", "rate": "+25%"},
        {"name": "sunhi_p45_r25", "voice": "ko-KR-SunHiNeural", "pitch": "+45Hz", "rate": "+25%"},
        {"name": "sunhi_p50_r30", "voice": "ko-KR-SunHiNeural", "pitch": "+50Hz", "rate": "+30%"},
        {"name": "sunhi_pct_p35pct_r20pct", "voice": "ko-KR-SunHiNeural", "pitch": "+35%", "rate": "+20%"},
        # Multilingual tests on Korean text
        {"name": "ava_multi_p35_r20", "voice": "en-US-AvaMultilingualNeural", "pitch": "+35Hz", "rate": "+20%"},
        {"name": "emma_multi_p35_r20", "voice": "en-US-EmmaMultilingualNeural", "pitch": "+35Hz", "rate": "+20%"},
        {"name": "hyunsu_multi_p35_r20", "voice": "ko-KR-HyunsuMultilingualNeural", "pitch": "+35Hz", "rate": "+20%"},
    ]
    
    for cfg in configs:
        text = test_sentences[0]
        out_path = os.path.join(OUTPUT_DIR, f"{cfg['name']}.mp3")
        try:
            comm = edge_tts.Communicate(text, cfg["voice"], pitch=cfg["pitch"], rate=cfg["rate"])
            await comm.save(out_path)
            size = os.path.getsize(out_path)
            print(f"Generated {cfg['name']}: size={size} bytes")
        except Exception as e:
            print(f"Failed {cfg['name']}: {e}")

if __name__ == "__main__":
    asyncio.run(test_voices_and_pitches())
