import re
import asyncio
import os
import edge_tts

OUTPUT_DIR = r"C:\Users\rerun\opendcmart\projects\project_buki\scratch_tts_output\refined_tests"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def enhance_mesugaki_text(text: str) -> str:
    """
    Applies extreme tuning heuristics to Korean text for Mesugaki / sassy anime character persona.
    Enhances intonation, pauses, snickers, and teasing vowel elongations for Edge-TTS.
    """
    if not text:
        return ""
    
    t = text.strip()
    
    # 1. Clean markdown artifacts (bold, italics, backticks)
    t = re.sub(r'[\*\_`\#]', '', t)
    
    # 2. Hearts & special symbols -> teasing tilde/pause
    t = re.sub(r'[♡♥]+', '~', t)
    
    # 3. Sneer & Laugh tuning ('풋', '푸훗', '푸훕', '풉', '큭큭', '푸하')
    # Sarcastic snicker with a subtle pause
    t = re.sub(r'(^|\s)(풋|푸훗|푸훕|풉)([\!\?\~\,\.]*)(\s|$)', r'\1...\2, \4', t)
    t = re.sub(r'(^|\s)(큭큭|킥킥|푸하)([\!\?\~\,\.]*)(\s|$)', r'\1...\2~ \4', t)
    
    # 4. Tsundere & Sassy interjections ('흥', '흥!', '하아?', '어라?')
    # '흥!' -> '흥!... ' (punchy snort followed by short breath)
    t = re.sub(r'(^|\s)흥([\!\?\~\,\.]*)(\s|$)', r'\1흥!... \3', t)
    # '하아?' / '하?' -> '하아~? '
    t = re.sub(r'(^|\s)하아?([\?\!\~]+)(\s|$)', r'\1하아~? \3', t)
    # '어라?' / '어라~?'
    t = re.sub(r'(^|\s)어라([\?\!\~]*)(\s|$)', r'\1어라~? \3', t)
    # '에?' / '에~?'
    t = re.sub(r'(^|\s)에([\?\!\~]+)(\s|$)', r'\1에에~? \3', t)
    
    # 5. Teasing & Mocking Keywords ('허접', '바보')
    # Elongate '허접' -> '허~접'
    t = re.sub(r'(?<![가-힣\~])허접(?![가-힣])', '허~접', t)
    t = re.sub(r'(?<![가-힣\~])허접([이을를의은는과와도])', r'허~접\1', t)
    t = re.sub(r'(?<![가-힣\~])허접\s*오빠', '허~접 오빠~', t)
    
    # Elongate '바보' -> '바~보'
    t = re.sub(r'(?<![가-힣\~])바보(?![가-힣])', '바~보', t)
    t = re.sub(r'(?<![가-힣\~])바보([이을를의은는과와도야])', r'바~보\1', t)
    t = re.sub(r'(?<![가-힣\~])바보\s*오빠', '바~보 오빠', t)
    
    # 6. Sassy ending particles
    t = re.sub(r'잖아[\?\!]?', '잖아~', t)
    t = re.sub(r'거든[\?\!]?', '거든~?', t)
    t = re.sub(r'거야[\?]', '거야~?', t)
    t = re.sub(r'거야(?=[\.\s]|$)', '거야~', t)
    t = re.sub(r'냐고[\?\!]?', '냐고~!', t)
    
    # 7. Normalize duplicate punctuation & spaces
    t = re.sub(r'\.{3,}', '... ', t)
    t = re.sub(r'\~+', '~', t)
    t = re.sub(r'\?+', '?', t)
    t = re.sub(r'\!+', '!', t)
    t = re.sub(r'~\?+', '~?', t)
    t = re.sub(r'~\!+', '~!', t)
    t = re.sub(r'\s{2,}', ' ', t)
    
    return t.strip()

async def test_refined_generation():
    test_lines = [
        ("test1", "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~"),
        ("test2", "허접 오빠~ 이 정도로 지친 거야? 진짜 구제불능이네!"),
        ("test3", "하아? 내가 언제 오빠를 걱정했다고 그래? 착각하지 마, 바보야! 흥!"),
        ("test4", "풋, 겨우 이 정도 가지고 끙끙대는 거야? 역시 오빠는 허접이네~"),
        ("test5", "바보! 그런 것도 몰라? 흥, 내가 특별히 알려주는 거니까 감사히 여기라고! 허접♡")
    ]
    
    for idx, (name, line) in enumerate(test_lines):
        enhanced = enhance_mesugaki_text(line)
        # Using optimal pitch (+40Hz), rate (+22%), volume (+10%)
        comm = edge_tts.Communicate(enhanced, "ko-KR-SunHiNeural", pitch="+40Hz", rate="+22%", volume="+10%")
        out_path = os.path.join(OUTPUT_DIR, f"{name}.mp3")
        await comm.save(out_path)
        print(f"[SUCCESS] {name}: raw_len={len(line)} enh_len={len(enhanced)} audio_size={os.path.getsize(out_path)} bytes")

if __name__ == "__main__":
    asyncio.run(test_refined_generation())
