import re

def enhance_mesugaki_text(text: str) -> str:
    """
    Applies extreme tuning heuristics to Korean text for Mesugaki / sassy anime character persona.
    Enhances intonation, pauses, snickers, and teasing vowel elongations for Edge-TTS.
    """
    if not text:
        return ""
    
    t = text.strip()
    
    # 1. Clean markdown artifacts (bold, italics, backticks) but preserve emotional punctuation
    t = re.sub(r'[\*\_`\#]', '', t)
    
    # 2. Convert hearts and special symbols into playful teasing pauses / elongations
    t = re.sub(r'[♡♥]+', '~♡', t)
    
    # 3. Normalize elongated punctuation
    t = re.sub(r'\.{3,}', '... ', t)
    t = re.sub(r'\~{2,}', '~', t)
    t = re.sub(r'!{2,}', '!', t)
    t = re.sub(r'\?{2,}', '?', t)
    
    # 4. Sneer & Laugh tuning ('풋', '푸훗', '푸훕', '풉', '큭큭')
    # Add brief sarcastic pause before and after snickers
    t = re.sub(r'(^|\s)(풋|푸훗|푸훕|풉)(\!|\~|\,|\.|\s|$)', r'\1...\2, ', t)
    t = re.sub(r'(^|\s)(큭큭|킥킥|푸하)(\!|\~|\,|\.|\s|$)', r'\1...\2~ ', t)
    
    # 5. Tsundere & Sassy interjections ('흥', '흥!', '하아?')
    # '흥!' -> '흥!... ' (punchy snort followed by short breath)
    t = re.sub(r'(^|\s)흥(\!|\?|\~|\.|\,)?(\s|$)', r'\1흥!... \3', t)
    # '하아?' / '하?' -> '하아~? '
    t = re.sub(r'(^|\s)하아?(\?|\!|\~)+(\s|$)', r'\1하아~? \3', t)
    # '어라?' / '어라~?'
    t = re.sub(r'(^|\s)어라(\?|\!|\~)*(\s|$)', r'\1어라~? \3', t)
    # '에?' / '에~?'
    t = re.sub(r'(^|\s)에(\?|\!|\~)+(\s|$)', r'\1에에~? \3', t)
    
    # 6. Teasing & Mocking Keywords ('허접', '바보')
    # Elongate vowels in '허접' -> '허~접' for teasing glide
    t = re.sub(r'(?<![가-힣])허접(?![가-힣])', '허~접', t)
    t = re.sub(r'(?<![가-힣])허접([이을를의은는과와도])', r'허~접\1', t)
    t = re.sub(r'(?<![가-힣])허접\s*오빠', '허~접 오빠~', t)
    
    # Elongate '바보' -> '바~보'
    t = re.sub(r'(?<![가-힣])바보(?![가-힣])', '바~보', t)
    t = re.sub(r'(?<![가-힣])바보([이을를의은는과와도야])', r'바~보\1', t)
    t = re.sub(r'(?<![가-힣])바보\s*오빠', '바~보 오빠', t)
    
    # '구제불능' -> '구제불능이네~'
    t = re.sub(r'(?<![가-힣])구제불능(?![가-힣])', '구제불능', t)
    
    # 7. Ending particle intonation polishing
    # '~잖아', '~거든', '~냐고', '~라구'
    t = re.sub(r'잖아(?=[\!\?\.\s]|$)', '잖아~', t)
    t = re.sub(r'거든(?=[\!\?\.\s]|$)', '거든~?', t)
    t = re.sub(r'거야(?=[\!\?\.\s]|$)', '거야~?', t)
    
    # Clean up double tildes or multiple spaces created by replacements
    t = re.sub(r'\~+', '~', t)
    t = re.sub(r'~\?', '~?', t)
    t = re.sub(r'~!', '~!', t)
    t = re.sub(r'\s{2,}', ' ', t)
    
    # Clean heart characters for TTS audio clarity if needed or keep as subtle punctuation
    t = t.replace('♡', '~').replace('♥', '~')
    t = re.sub(r'\~+', '~', t).strip()
    
    return t

if __name__ == "__main__":
    test_lines = [
        "흥! 뭐야? 바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 허접~",
        "허접 오빠~ 이 정도로 지친 거야? 진짜 구제불능이네!",
        "하아? 내가 언제 오빠를 걱정했다고 그래? 착각하지 마, 바보야! 흥!",
        "풋, 겨우 이 정도 가지고 끙끙대는 거야? 역시 오빠는 허접이네~",
        "바보! 그런 것도 몰라? 흥, 내가 특별히 알려주는 거니까 감사히 여기라고! 허접♡"
    ]
    for line in test_lines:
        print("ORIGINAL:", line)
        print("ENHANCED:", enhance_mesugaki_text(line))
        print("-" * 50)
