import asyncio
import os
import edge_tts
from edge_tts.communicate import TTSConfig, ssml_headers_plus_data, connect_id

OUTPUT_DIR = r"C:\Users\rerun\opendcmart\projects\project_buki\scratch_tts_output"

async def test_custom_ssml(ssml_content: str, out_filename: str):
    import aiohttp
    import ssl
    import certifi
    from edge_tts.communicate import WSS_URL, WSS_HEADERS, DRM, get_headers_and_data, UnexpectedResponse

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    audio_bytes = bytearray()
    headers = {**WSS_HEADERS, "Pragma": "no-cache", "Cache-Control": "no-cache"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.ws_connect(
            f"{WSS_URL}&ConnectionId={connect_id()}",
            headers=headers,
            ssl=ssl_ctx,
        ) as ws:
            # Send config
            await ws.send_str(
                f"X-Timestamp:{edge_tts.communicate.date_to_string()}\r\n"
                "Content-Type:application/json; charset=utf-8\r\n"
                "Path:speech.config\r\n\r\n"
                '{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"false"},"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}\r\n'
            )

            # Send SSML
            await ws.send_str(
                ssml_headers_plus_data(
                    connect_id(),
                    edge_tts.communicate.date_to_string(),
                    ssml_content
                )
            )

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if b"turn.end" in msg.data.encode("utf-8"):
                        break
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    header_len = int.from_bytes(msg.data[:2], "big")
                    params, data = get_headers_and_data(msg.data, header_len)
                    if params.get(b"Path") == b"audio" and len(data) > 0:
                        audio_bytes.extend(data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"WS error: {msg.data}")
                    break

    if audio_bytes:
        with open(out_path, "wb") as f:
            f.write(audio_bytes)
        print(f"Successfully generated {out_filename}: {len(audio_bytes)} bytes")
    else:
        print(f"Failed {out_filename}: No audio received")

async def run_ssml_tests():
    # Test 1: Standard SSML with prosody pitch and rate
    ssml1 = """<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ko-KR'>
<voice name='ko-KR-SunHiNeural'>
<prosody pitch='+42Hz' rate='+25%' volume='+10%'>
흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~
</prosody>
</voice>
</speak>"""
    await test_custom_ssml(ssml1, "test_ssml_basic.mp3")

    # Test 2: Word-level pitch/rate prosody and break tags (Mesugaki expressions)
    ssml2 = """<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ko-KR'>
<voice name='ko-KR-SunHiNeural'>
<prosody pitch='+38Hz' rate='+22%'>
<prosody pitch='+65Hz' rate='+35%'>흥!</prosody> <break time='120ms'/>
뭐야?
<prosody pitch='+45Hz' rate='+25%'>바~보 오빠,</prosody> <break time='80ms'/>
아직도 그거 하나 이해 못 한 거야?
<break time='150ms'/>
<prosody pitch='+55Hz' rate='+15%'>풋~,</prosody> <break time='80ms'/>
<prosody pitch='+60Hz' rate='+10%'>허~접♡</prosody>
</prosody>
</voice>
</speak>"""
    await test_custom_ssml(ssml2, "test_ssml_advanced.mp3")

    # Test 3: Korean expressiveness with contour / express-as if supported
    ssml3 = """<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='ko-KR'>
<voice name='ko-KR-SunHiNeural'>
<prosody pitch='+40Hz' rate='+25%'>
<prosody pitch='+70Hz' rate='+30%'>흥!</prosody> <break time='100ms'/>
<prosody pitch='+35Hz'>허접 오빠~</prosody> <break time='100ms'/>
이 정도로 지친 거야? <break time='120ms'/>
<prosody pitch='+50Hz' rate='+30%'>진짜 구제불능이네!</prosody>
</prosody>
</voice>
</speak>"""
    await test_custom_ssml(ssml3, "test_ssml_dynamic.mp3")

if __name__ == "__main__":
    asyncio.run(run_ssml_tests())
