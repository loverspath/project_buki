import asyncio
import os
import edge_tts

OUTPUT_DIR = r"C:\Users\rerun\opendcmart\projects\project_buki\scratch_tts_output"

class CustomSSMLCommunicate(edge_tts.Communicate):
    def __init__(self, raw_ssml_body: str, voice: str = "ko-KR-SunHiNeural", pitch: str = "+0Hz", rate: str = "+0%", volume: str = "+0%"):
        super().__init__("placeholder", voice=voice, pitch=pitch, rate=rate, volume=volume)
        # Directly set unescaped SSML body
        self.texts = [raw_ssml_body]

async def test_ssml_capabilities():
    # Test A: Basic nested prosody
    body_a = "<prosody pitch='+70Hz' rate='+35%'>흥!</prosody> <break time='200ms'/> 뭐야? <prosody pitch='+50Hz'>바보 오빠,</prosody> 아직도 그거 하나 이해 못 한 거야? <break time='300ms'/> <prosody pitch='+55Hz' rate='+15%'>풋~,</prosody> <prosody pitch='+65Hz' rate='-10%'>허~접♡</prosody>"
    
    comm_a = CustomSSMLCommunicate(body_a, voice="ko-KR-SunHiNeural", pitch="+40Hz", rate="+25%")
    out_a = os.path.join(OUTPUT_DIR, "test_custom_ssml_a.mp3")
    await comm_a.save(out_a)
    print("A generated, size:", os.path.getsize(out_a))

    # Test B: SSML with emphasis and pitch contours
    body_b = "<emphasis level='strong'>흥!</emphasis> <break time='150ms'/> <prosody pitch='+45Hz'>허접 오빠~</prosody> 이 정도로 지친 거야? <break time='200ms'/> 진짜 <prosody pitch='+60Hz' rate='+30%'>구제불능</prosody>이네!"
    comm_b = CustomSSMLCommunicate(body_b, voice="ko-KR-SunHiNeural", pitch="+38Hz", rate="+22%")
    out_b = os.path.join(OUTPUT_DIR, "test_custom_ssml_b.mp3")
    await comm_b.save(out_b)
    print("B generated, size:", os.path.getsize(out_b))

if __name__ == "__main__":
    asyncio.run(test_ssml_capabilities())
