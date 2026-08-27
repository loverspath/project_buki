import asyncio
import os
import edge_tts

OUTPUT_DIR = r"C:\Users\rerun\opendcmart\projects\project_buki\scratch_tts_output"

test_cases = [
    # Baseline vs tuned pitch/rate
    ("base_raw", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+0Hz", "+0%"),
    ("tuned_p35_r20", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+35Hz", "+20%"),
    ("tuned_p40_r22", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+40Hz", "+22%"),
    ("tuned_p42_r25", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+42Hz", "+25%"),
    ("tuned_p45_r25", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+45Hz", "+25%"),
    
    # Preprocessing variations on p42_r25
    # 1. Punctuation & Pauses
    ("prep_v1_pauses", "흥! ...뭐야? 바~보 오빠. 아직도 그거 하나 이해 못 한 거야? ...풋! 허~접~", "+42Hz", "+25%"),
    # 2. Exclamation & Teasing
    ("prep_v2_tease", "흥! 뭐야? 바~보 오빠, 아직도 그거 하나 이해 못 한 거야~? 풋, 허~접♡", "+42Hz", "+25%"),
    # 3. Sneering laugh & breath
    ("prep_v3_sneer", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못한 거야? 푸훕... 완전 허~접이네!", "+42Hz", "+25%"),
    # 4. Tsundere anger
    ("prep_v4_anger", "하아?! 내가 언제 오빠 걱정했다고 그래? 착각하지 마, 바~보야! 흥!", "+42Hz", "+25%"),
    # 5. Heart & playful mockery
    ("prep_v5_smug", "어라~? 이 정도로 지친 거야? 진짜 허접이네~ 푸하, 힘내 봐, 바보 오빠!", "+42Hz", "+25%"),
]

async def run_tuning_tests():
    for name, text, pitch, rate in test_cases:
        out_path = os.path.join(OUTPUT_DIR, f"{name}.mp3")
        try:
            comm = edge_tts.Communicate(text, "ko-KR-SunHiNeural", pitch=pitch, rate=rate)
            await comm.save(out_path)
            print(f"[GENERATED] {name:18} | Pitch: {pitch:6} | Rate: {rate:6} | Size: {os.path.getsize(out_path):6} bytes")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")

if __name__ == "__main__":
    asyncio.run(run_tuning_tests())
