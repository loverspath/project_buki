# -*- coding: utf-8 -*-
"""
Project BUKI - Automated 1-Click GPT-SoVITS Fine-Tuning Pipeline for Tenko Shibuki
Runs Stage 1A (Text), 1B (HuBERT), 1C (Semantic), 2A (SoVITS VITS), and 2B (GPT AR).
"""
import os
import sys
import json
import yaml
import time
import subprocess
from pathlib import Path

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')

GPT_SOVITS_DIR = Path(r"C:\Users\rerun\opendcmart\tools\GPT-SoVITS")
PYTHON_EXEC = GPT_SOVITS_DIR / ".venv" / "Scripts" / "python.exe"
EXP_NAME = "shibuki"

BUKI_DIR = Path(r"C:\Users\rerun\opendcmart\projects\project_buki")
LIST_PATH = BUKI_DIR / "src" / "assets" / "voice_samples" / "shibuki" / "shibuki.list"
WAV_DIR = BUKI_DIR / "src" / "assets" / "voice_samples" / "shibuki"
OPT_DIR = GPT_SOVITS_DIR / "output" / EXP_NAME

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["is_half"] = "True"
os.environ["version"] = "v2"

def log(msg, symbol="🚀"):
    print(f"\n{symbol} [{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def run_step(cmd, env_vars=None, step_name=""):
    log(f"Starting {step_name}...", "⏳")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    
    # Ensure GPT_SoVITS is on PYTHONPATH
    python_paths = [str(GPT_SOVITS_DIR), str(GPT_SOVITS_DIR / "GPT_SoVITS")]
    if "PYTHONPATH" in env:
        python_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = ";".join(python_paths)

    if env_vars:
        env.update(env_vars)
    
    start_t = time.time()
    p = subprocess.Popen(
        cmd,
        cwd=str(GPT_SOVITS_DIR),
        env=env,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    
    for line in iter(p.stdout.readline, ""):
        line_s = line.strip()
        if line_s:
            print(f"  [Log] {line_s}", flush=True)
    
    p.wait()
    elapsed = time.time() - start_t
    if p.returncode == 0:
        log(f"{step_name} completed successfully in {elapsed:.1f}s!", "✅")
    else:
        log(f"{step_name} exited with code {p.returncode} ({elapsed:.1f}s)", "❌")
    return p.returncode

def main():
    print("=" * 65)
    print("  🦊 Project BUKI - Tenko Shibuki GPT-SoVITS Fine-Tuning Pipeline")
    print("=" * 65)

    os.makedirs(OPT_DIR, exist_ok=True)

    # ----------------------------------------------------
    # Stage 1A: 1-get-text.py
    # ----------------------------------------------------
    env_1a = {
        "inp_text": str(LIST_PATH),
        "inp_wav_dir": str(WAV_DIR),
        "exp_name": EXP_NAME,
        "opt_dir": str(OPT_DIR),
        "bert_pretrained_dir": str(GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models" / "chinese-roberta-wwm-ext-large"),
        "i_part": "0",
        "all_parts": "1",
        "_CUDA_VISIBLE_DEVICES": "0",
        "is_half": "True",
        "version": "v2"
    }
    ret = run_step(f'"{PYTHON_EXEC}" -s GPT_SoVITS/prepare_datasets/1-get-text.py', env_1a, "Stage 1A: Text Tokenization & Phoneme Extraction")
    if ret != 0: return

    # Merge text output
    txt_part = OPT_DIR / "2-name2text-0.txt"
    txt_main = OPT_DIR / "2-name2text.txt"
    if txt_part.exists():
        txt_main.write_text(txt_part.read_text(encoding="utf-8"), encoding="utf-8")
        txt_part.unlink()

    # ----------------------------------------------------
    # Stage 1B: 2-get-hubert-wav32k.py
    # ----------------------------------------------------
    env_1b = {
        "inp_text": str(LIST_PATH),
        "inp_wav_dir": str(WAV_DIR),
        "exp_name": EXP_NAME,
        "opt_dir": str(OPT_DIR),
        "cnhubert_base_dir": str(GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models" / "chinese-hubert-base"),
        "i_part": "0",
        "all_parts": "1",
        "_CUDA_VISIBLE_DEVICES": "0",
        "is_half": "True"
    }
    ret = run_step(f'"{PYTHON_EXEC}" -s GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py', env_1b, "Stage 1B: HuBERT SSL Features & 32kHz Resampling")
    if ret != 0: return

    # ----------------------------------------------------
    # Stage 1C: 3-get-semantic.py
    # ----------------------------------------------------
    env_1c = {
        "inp_text": str(LIST_PATH),
        "exp_name": EXP_NAME,
        "opt_dir": str(OPT_DIR),
        "pretrained_s2G": str(GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models" / "gsv-v2final-pretrained" / "s2G2333k.pth"),
        "s2config_path": str(GPT_SOVITS_DIR / "GPT_SoVITS" / "configs" / "s2.json"),
        "i_part": "0",
        "all_parts": "1",
        "_CUDA_VISIBLE_DEVICES": "0",
        "is_half": "True"
    }
    ret = run_step(f'"{PYTHON_EXEC}" -s GPT_SoVITS/prepare_datasets/3-get-semantic.py', env_1c, "Stage 1C: Semantic Token Representation Extraction")
    if ret != 0: return

    # Merge semantic output
    sem_part = OPT_DIR / "6-name2semantic-0.tsv"
    sem_main = OPT_DIR / "6-name2semantic.tsv"
    if sem_part.exists():
        sem_main.write_text(sem_part.read_text(encoding="utf-8"), encoding="utf-8")
        sem_part.unlink()

    # ----------------------------------------------------
    # Stage 2A: SoVITS Fine-Tuning (s2_train.py)
    # ----------------------------------------------------
    s2_config_template = GPT_SOVITS_DIR / "GPT_SoVITS" / "configs" / "s2.json"
    with open(s2_config_template, "r", encoding="utf-8") as f:
        s2_data = json.load(f)

    s2_weights_dir = GPT_SOVITS_DIR / "SoVITS_weights_v2"
    os.makedirs(s2_weights_dir, exist_ok=True)
    import shutil
    logs_s1 = OPT_DIR / "logs_s1_v2"
    logs_s2 = OPT_DIR / "logs_s2_v2"
    if logs_s1.exists():
        shutil.rmtree(logs_s1, ignore_errors=True)
    if logs_s2.exists():
        shutil.rmtree(logs_s2, ignore_errors=True)
    os.makedirs(logs_s2, exist_ok=True)
    os.makedirs(logs_s1, exist_ok=True)

    s2_data["train"]["batch_size"] = 8
    s2_data["train"]["epochs"] = 8
    s2_data["train"]["text_low_lr_rate"] = 0.4
    s2_data["train"]["pretrained_s2G"] = str(GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models" / "gsv-v2final-pretrained" / "s2G2333k.pth")
    s2_data["train"]["pretrained_s2D"] = str(GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models" / "gsv-v2final-pretrained" / "s2D2333k.pth")
    s2_data["train"]["if_save_latest"] = True
    s2_data["train"]["if_save_every_weights"] = True
    s2_data["train"]["save_every_epoch"] = 4
    s2_data["train"]["gpu_numbers"] = "0"
    s2_data["data"]["exp_dir"] = str(OPT_DIR)
    s2_data["data"]["version"] = "v2"
    s2_data["model"]["version"] = "v2"
    s2_data["s2_ckpt_dir"] = str(OPT_DIR)
    s2_data["save_weight_dir"] = str(s2_weights_dir)
    s2_data["name"] = EXP_NAME
    s2_data["version"] = "v2"

    tmp_s2_json = GPT_SOVITS_DIR / "TEMP" / "tmp_s2.json"
    os.makedirs(tmp_s2_json.parent, exist_ok=True)
    with open(tmp_s2_json, "w", encoding="utf-8") as f:
        json.dump(s2_data, f, indent=2)

    ret = run_step(f'"{PYTHON_EXEC}" -s GPT_SoVITS/s2_train.py --config "{tmp_s2_json}"', None, "Stage 2A: SoVITS Decoder Acoustic Fine-Tuning (8 Epochs)")
    if ret != 0: return

    # ----------------------------------------------------
    # Stage 2B: GPT AR Fine-Tuning (s1_train.py)
    # ----------------------------------------------------
    s1_config_template = GPT_SOVITS_DIR / "GPT_SoVITS" / "configs" / "s1longer-v2.yaml"
    with open(s1_config_template, "r", encoding="utf-8") as f:
        s1_data = yaml.load(f, Loader=yaml.FullLoader)

    gpt_weights_dir = GPT_SOVITS_DIR / "GPT_weights_v2"
    os.makedirs(gpt_weights_dir, exist_ok=True)

    s1_data["train"]["batch_size"] = 8
    s1_data["train"]["epochs"] = 15
    s1_data["pretrained_s1"] = str(GPT_SOVITS_DIR / "GPT_SoVITS" / "pretrained_models" / "gsv-v2final-pretrained" / "s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt")
    s1_data["train"]["save_every_n_epoch"] = 5
    s1_data["train"]["if_save_every_weights"] = True
    s1_data["train"]["if_save_latest"] = True
    s1_data["train"]["if_dpo"] = False
    s1_data["train"]["half_weights_save_dir"] = str(gpt_weights_dir)
    s1_data["train"]["exp_name"] = EXP_NAME
    s1_data["train_semantic_path"] = str(OPT_DIR / "6-name2semantic.tsv")
    s1_data["train_phoneme_path"] = str(OPT_DIR / "2-name2text.txt")
    s1_data["output_dir"] = str(OPT_DIR / "logs_s1_v2")

    tmp_s1_yaml = GPT_SOVITS_DIR / "TEMP" / "tmp_s1.yaml"
    with open(tmp_s1_yaml, "w", encoding="utf-8") as f:
        yaml.dump(s1_data, f, default_flow_style=False)

    env_s1 = {
        "_CUDA_VISIBLE_DEVICES": "0",
        "hz": "25hz"
    }
    ret = run_step(f'"{PYTHON_EXEC}" -s GPT_SoVITS/s1_train.py --config_file "{tmp_s1_yaml}"', env_s1, "Stage 2B: GPT Autoregressive Prosody Fine-Tuning (15 Epochs)")
    if ret != 0: return

    print("\n" + "=" * 65)
    print("  🎉 [SUCCESS] Tenko Shibuki GPT-SoVITS Fine-Tuning Finished!")
    print(f"  - SoVITS Weight Saved: {s2_weights_dir}")
    print(f"  - GPT Weight Saved:    {gpt_weights_dir}")
    print("=" * 65)

if __name__ == "__main__":
    main()
