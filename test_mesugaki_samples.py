import asyncio
import os
import edge_tts

OUTPUT_DIR = r"C:\Users\rerun\opendcmart\projects\project_buki\scratch_tts_output\tuning_samples"
os.makedirs(OUTPUT_DIR, exist_ok=True)

samples = [
    # 1. Comparison of pitch levels for SunHi
    ("pitch_35", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+35Hz", "+22%"),
    ("pitch_38", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+38Hz", "+24%"),
    ("pitch_40", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+40Hz", "+25%"),
    ("pitch_42", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+42Hz", "+25%"),
    ("pitch_45", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+45Hz", "+26%"),

    # 2. Preprocessing enhancement comparisons
    # Sample A: '흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~'
    ("sample_a_raw", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~", "+40Hz", "+25%"),
    ("sample_a_enhanced", "흥!... 뭐야? 바~보 오빠, 아직도 그거 하나 이해 못 한 거야~? ...푸훕, 완전 허~접~!", "+40Hz", "+25%"),

    # Sample B: '허접 오빠~ 이 정도로 지친 거야? 진짜 구제불능이네!'
    ("sample_b_raw", "허접 오빠~ 이 정도로 지친 거야? 진짜 구제불능이네!", "+40Hz", "+25%"),
    ("sample_b_enhanced", "허~접 오빠~? 이 정도로 지친 거야~? ...풋, 진짜 구제불능이네~!", "+40Hz", "+25%"),

    # Sample C: '하아? 내가 언제 오빠를 걱정했다고 그래? 착각하지 마, 바보야! 흥!'
    ("sample_c_raw", "하아? 내가 언제 오빠를 걱정했다고 그래? 착각하지 마, 바보야! 흥!", "+40Hz", "+25%"),
    ("sample_c_enhanced", "하아~? 내가 언제 오빠를 걱정했다고 그래? 착각하지 마, 바~보야! ...흥!", "+40Hz", "+25%"),

    # Sample D: '바보! 그런 것도 몰라? 흥, 내가 특별히 알려주는 거니까 감사히 여기라고!'
    ("sample_d_raw", "바보! 그런 것도 몰라? 흥, 내가 특별히 알려주는 거니까 감사히 여기라고!", "+40Hz", "+25%"),
    ("sample_d_enhanced", "바~보! 그런 것도 몰라~? 흥!... 내가 특별~히 알려주는 거니까 감사히 여기라고!", "+40Hz", "+25%"),
]

async def generate_all_samples():
    for name, text, pitch, rate in samples:
        out_file = os.path.join(OUTPUT_DIR, f"{name}.mp3")
        try:
            comm = edge_tts.Communicate(text, "ko-KR-SunHiNeural", pitch=pitch, rate=rate)
            await comm.save(out_file)
            print(f"[OK] {name:20} -> {os.path.getsize(out_file)} bytes")
        except Exception as e:
            print(f"[ERR] {name:20} -> {e}")

if __name__ == "__main__":
    asyncio.run(generate_all_samples())
