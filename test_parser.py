# -*- coding: utf-8 -*-
import re
from typing import Tuple, List

def is_bracket_balanced(text: str) -> bool:
    if text.count('(') > text.count(')'): return False
    if text.count('[') > text.count(']'): return False
    if text.count('{') > text.count('}'): return False
    if text.count('〈') > text.count('〉'): return False
    if text.count('《') > text.count('》'): return False
    if text.count('*') % 2 != 0: return False
    return True

def is_safe_sentence_boundary(buffer: str) -> bool:
    if not is_bracket_balanced(buffer):
        return False
    if re.search(r'([.!?！？\n]+)\s*$', buffer):
        return True
    if re.search(r'(~+)\s*$', buffer) and len(buffer.strip()) >= 6:
        return True
    return False

def parse_dialogue_and_actions(text: str) -> Tuple[str, List[str]]:
    action_matches = re.findall(r'[\(\[\*〈《]([^\)\]\*〉》]+)[\)\]\*〉》]', text)
    actions = [a.strip() for a in action_matches if a.strip()]

    cleaned = re.sub(r'\([^\)]*\)|\[[^\]]*\]|\*[^\*]*\*|\<[^\>]*\>|〈[^〉]*〉|《[^》]*》', ' ', text)
    cleaned = re.sub(r'[\(\[\*〈《][^\)\]\*〉》]*$', '', cleaned)
    cleaned = re.sub(r'^(대사|말|응답)\s*:\s*', '', cleaned)
    clean_speech = re.sub(r'[\*\#\_`\"]', '', cleaned).strip()
    clean_speech = re.sub(r'\s+', ' ', clean_speech).strip()
    has_pronounceable = bool(re.search(r'[가-힣a-zA-Z0-9]', clean_speech))
    if not has_pronounceable:
        clean_speech = ""
    return clean_speech, actions

if __name__ == '__main__':
    cases = [
        '(팔짱을 끼며 비웃는다.) 뭐야, 바보 오빠?',
        '(그리고 오빠에게 꿀밤을 한 대 콩, 때리고는 고개를 돌린다.',
        '*한숨을 푹 쉬며* 완전 허접이네~',
        '(그냥 조용히 째려본다)',
        '바보 오빠, 아직도 그거 하나 이해 못 한 거야? 풋, 완전 허접이네~'
    ]

    print("=== Dialogue Parser Verification ===")
    for c in cases:
        speech, acts = parse_dialogue_and_actions(c)
        print(f"Input:  {c}")
        print(f"Speech: [{speech}] (Actions: {acts})")
        print("-" * 40)

    # Streaming simulation test
    stream_tokens = ['(', '그리고 ', '오빠에게 ', '꿀밤을 ', '한 대 콩, ', '때리고는 ', '고개를 ', '돌린다.', ') ', '뭐야, ', '바보 ', '오빠!']
    buf = ""
    chunks_sent = []
    for tok in stream_tokens:
        buf += tok
        if is_safe_sentence_boundary(buf):
            sp, ac = parse_dialogue_and_actions(buf)
            chunks_sent.append((sp, ac))
            buf = ""
    if buf.strip():
        sp, ac = parse_dialogue_and_actions(buf)
        if sp or ac:
            chunks_sent.append((sp, ac))

    print("\n=== Streaming Sentence Splitting Simulation ===")
    for i, (sp, ac) in enumerate(chunks_sent):
        print(f"Chunk #{i+1}: Speech=[{sp}] | Actions={ac}")
