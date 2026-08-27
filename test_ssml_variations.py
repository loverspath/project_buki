import asyncio
import os
import edge_tts

OUTPUT_DIR = r"C:\Users\rerun\opendcmart\projects\project_buki\scratch_tts_output"

class RawSSMLCommunicate(edge_tts.Communicate):
    def __init__(self, raw_body: str, voice: str = "ko-KR-SunHiNeural", pitch: str = "+40Hz", rate: str = "+25%"):
        super().__init__("placeholder", voice=voice, pitch=pitch, rate=rate)
        self.texts = [raw_body]

async def test_ssml_variations():
    tests = [
        # 1. Plain text with special characters and punctuation
        ("plain_tilde_excl", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~"),
        ("plain_heart", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접♡"),
        ("plain_dots", "흥! 뭐야...? 바보 오빠... 아직도 그거 하나 이해 못 한 거야? 풋... 허접~~"),
        ("plain_respelled", "흥! 뭐야? 바~아보 오빠! 아직도 그거 하나 이해 못 한 거야? 푸훕, 허-접~"),
        
        # 2. SSML Break only
        ("ssml_break", "흥! <break time='200ms'/> 뭐야? 바보 오빠! <break time='150ms'/> 풋, 허접!"),
        
        # 3. SSML Break strength
        ("ssml_break_strength", "흥! <break strength='strong'/> 뭐야? 바보 오빠! <break strength='medium'/> 풋, 허접!"),
        
        # 4. SSML nested prosody
        ("ssml_nested_prosody", "<prosody pitch='+60Hz'>흥!</prosody> 뭐야? <prosody pitch='+50Hz'>바보 오빠!</prosody> 풋, 허접!"),
        
        # 5. SSML emphasis
        ("ssml_emphasis", "<emphasis level='strong'>흥!</emphasis> 뭐야? 바보 오빠! 풋, 허접!"),
        
        # 6. SSML say-as
        ("ssml_say_as", "흥! 뭐야? 바보 오빠! 풋, <say-as interpret-as='characters'>허접</say-as>!"),
    ]

    for name, body in tests:
        out_path = os.path.join(OUTPUT_DIR, f"{name}.mp3")
        try:
            if "ssml_" in name:
                comm = RawSSMLCommunicate(body, voice="ko-KR-SunHiNeural", pitch="+40Hz", rate="+25%")
            else:
                comm = edge_tts.Communicate(body, voice="ko-KR-SunHiNeural", pitch="+40Hz", rate="+25%")
            await comm.save(out_path)
            print(f"[SUCCESS] {name}: size={os.path.getsize(out_path)} bytes")
        except Exception as e:
            print(f"[FAIL] {name}: {type(e).__name__} - {e}")

if __name__ == "__main__":
    asyncio.run(test_ssml_variations())
