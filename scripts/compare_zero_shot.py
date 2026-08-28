# -*- coding: utf-8 -*-
import os, sys, json, urllib.request, urllib.parse
from pathlib import Path

base_dir = Path(r"C:\Users\rerun\opendcmart\projects\project_buki")
shibuki_ref = "C:/Users/rerun/opendcmart/projects/project_buki/src/assets/voice_samples/shibuki/shibuki_sample_014.wav"
prompt_text = "대박 대박 대박 구했습니다! 하하!"

test_cases = [
    {
        "name": "1_Pure_Base_Zeroshot",
        "desc": "공식 파운데이션 베이스 모델 (s2G2333k.pth) + 시부키 3초 제로샷",
        "sovits": "C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth",
        "gpt": "C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt"
    },
    {
        "name": "2_Hachikuji_Mesugaki_Zeroshot",
        "desc": "하치쿠지 마요이(메스가키) 사전학습 모델 + 시부키 3초 제로샷",
        "sovits": "C:/Users/rerun/opendcmart/tools/GPT-SoVITS/SoVITS_weights_v2/hachikuji_mesugaki.pth",
        "gpt": "C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_weights_v2/hachikuji_mesugaki.ckpt"
    },
    {
        "name": "3_Rimuru_Zeroshot",
        "desc": "리무루(소녀톤) 사전학습 모델 + 시부키 3초 제로샷",
        "sovits": "C:/Users/rerun/opendcmart/tools/GPT-SoVITS/SoVITS_weights_v2/rimuru_e20_s160.pth",
        "gpt": "C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_weights_v2/rimuru-e15.ckpt"
    },
    {
        "name": "4_Direct_Shibuki_Finetuned",
        "desc": "시부키 105개 청정 데이터셋 직접 파인튜닝 전용 모델",
        "sovits": "C:/Users/rerun/opendcmart/tools/GPT-SoVITS/SoVITS_weights_v2/shibuki_e12_s636.pth",
        "gpt": "C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_weights_v2/shibuki-e20.ckpt"
    }
]

for tc in test_cases:
    case_name = tc["name"]
    print(f"\n==================================================")
    print(f"  [Test] {case_name}")
    print(f"  [Desc] {tc['desc']}")
    print(f"==================================================")
    
    encoded_s = urllib.parse.quote(tc["sovits"])
    encoded_g = urllib.parse.quote(tc["gpt"])
    url_s = f"http://127.0.0.1:9880/set_sovits_weights?weights_path={encoded_s}"
    url_g = f"http://127.0.0.1:9880/set_gpt_weights?weights_path={encoded_g}"
    
    r_s = urllib.request.urlopen(url_s)
    r_g = urllib.request.urlopen(url_g)
    print(f"  -> Model Hotswap OK: SoVITS({r_s.status}), GPT({r_g.status})")
    
    payload = {
        "text": "안녕하세요 여러분! 텐코 시부키예요. 오늘 방송도 재미있게 봐주세요!",
        "text_lang": "all_ko",
        "ref_audio_path": shibuki_ref,
        "prompt_text": prompt_text,
        "prompt_lang": "all_ko",
        "top_k": 10,
        "top_p": 0.80,
        "temperature": 0.65,
        "speed_factor": 1.0,
        "text_split_method": "cut5",
        "batch_size": 1,
        "media_type": "wav",
        "streaming_mode": False
    }
    
    req = urllib.request.Request(
        "http://127.0.0.1:9880/tts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        wav_bytes = resp.read()
        out_f = base_dir / f"compare_{case_name}.wav"
        out_f.write_bytes(wav_bytes)
        print(f"  -> Generated: {out_f.name} ({len(wav_bytes)} bytes)")
