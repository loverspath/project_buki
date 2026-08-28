# -*- coding: utf-8 -*-
"""
Project BUKI - Voice Sample Curator & Dataset Studio Backend Manager
Provides lossless 0.1s wave trimming, transcription syncing, inclusion toggling,
and curation manifest persistence.
"""
import os
import sys
import wave
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).parent.parent
SAMPLES_DIR = BASE_DIR / "assets" / "voice_samples" / "shibuki_dataset"
CLIPS_DIR = SAMPLES_DIR / "clips"
BACKUP_DIR = SAMPLES_DIR / "backup"
MANIFEST_FILE = SAMPLES_DIR / "curation_manifest.json"
SHIBUKI_LIST_FILE = SAMPLES_DIR / "shibuki.list"

# Legacy/Source Shibuki Dir
LEGACY_SHIBUKI_DIR = BASE_DIR / "assets" / "voice_samples" / "shibuki"

def init_dataset_structure():
    """Initializes dedicated clean dataset directory with clips."""
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # If clips dir is empty, migrate clean samples from legacy shibuki dir
    existing_clips = list(CLIPS_DIR.glob("*.wav"))
    if not existing_clips and LEGACY_SHIBUKI_DIR.exists():
        print("[Curator] Initializing dedicated dataset clips directory from legacy folder...")
        for wav_file in sorted(LEGACY_SHIBUKI_DIR.glob("shibuki_sample_*.wav")):
            if "backup" in wav_file.name or "test" in wav_file.name:
                continue
            shutil.copy2(wav_file, CLIPS_DIR / wav_file.name)
            # Create original backup
            shutil.copy2(wav_file, BACKUP_DIR / wav_file.name)

    # Also load initial transcripts if manifest doesn't exist
    if not MANIFEST_FILE.exists():
        manifest_data = {"samples": [], "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")}
        
        # Load legacy transcripts from shibuki.list or voice_manifest.json if available
        legacy_transcripts = {}
        legacy_list = LEGACY_SHIBUKI_DIR / "shibuki.list"
        if legacy_list.exists():
            try:
                for line in legacy_list.read_text(encoding="utf-8").splitlines():
                    parts = line.strip().split("|")
                    if len(parts) >= 4:
                        fname = Path(parts[0]).name
                        legacy_transcripts[fname] = parts[3].strip()
            except Exception as e:
                print(f"[Curator] Warning reading legacy list: {e}")

        # Build initial manifest
        for wav_file in sorted(CLIPS_DIR.glob("shibuki_sample_*.wav")):
            fname = wav_file.name
            dur = get_wav_duration(wav_file)
            txt = legacy_transcripts.get(fname, "")
            
            # Special user-custom samples
            if fname == "shibuki_sample_114.wav":
                txt = "뽑아주고 그 내가 뭔가 나만의 각을 만들어"
            elif fname == "shibuki_sample_010.wav":
                txt = "여러분 밤을 주워 왔어요 상상도 못했져?"

            manifest_data["samples"].append({
                "sample_id": fname.replace(".wav", ""),
                "filename": fname,
                "duration": round(dur, 2),
                "transcript": txt,
                "emotion": "question" if "?" in txt else "neutral",
                "is_included": True,
                "trim_start": 0.0,
                "trim_end": round(dur, 2),
                "agent_notes": ""
            })
        
        save_manifest(manifest_data)

def get_wav_duration(file_path: Path) -> float:
    """Returns exact duration of a WAV file in seconds."""
    try:
        with wave.open(str(file_path), "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
            return frames / float(rate)
    except Exception:
        return 0.0

def load_manifest() -> Dict[str, Any]:
    """Loads the curation manifest JSON."""
    init_dataset_structure()
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Curator] Error loading manifest: {e}")
    return {"samples": [], "last_updated": ""}

def save_manifest(data: Dict[str, Any]):
    """Saves the curation manifest JSON and auto-generates shibuki.list."""
    data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Generate clean shibuki.list for training with only included samples
    export_training_list(data.get("samples", []))

def export_training_list(samples: List[Dict[str, Any]]):
    """Exports GPT-SoVITS training format dataset list file."""
    lines = []
    for s in samples:
        if s.get("is_included", True):
            fname = s.get("filename", "")
            clip_path = (CLIPS_DIR / fname).resolve().as_posix()
            transcript = s.get("transcript", "").strip()
            if transcript:
                lines.append(f"{clip_path}|shibuki|ko|{transcript}")
    
    SHIBUKI_LIST_FILE.write_text("\n".join(lines), encoding="utf-8")
    # Also sync to legacy folder for direct compatibility
    legacy_target = LEGACY_SHIBUKI_DIR / "shibuki.list"
    if legacy_target.parent.exists():
        legacy_target.write_text("\n".join(lines), encoding="utf-8")

def trim_wav_lossless(file_path: Path, start_sec: float, end_sec: float, out_path: Optional[Path] = None) -> float:
    """
    Losslessly trims a WAV file using Python's native wave module.
    0.1s precision, byte-exact slicing, preserving original sampling rate & bit depth.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"WAV file not found: {file_path}")

    target_out = out_path or file_path

    with wave.open(str(file_path), "rb") as win:
        params = win.getparams()
        nchannels, sampwidth, framerate, nframes, comptype, compname = params
        
        total_duration = nframes / float(framerate)
        start_sec = max(0.0, min(start_sec, total_duration))
        end_sec = max(start_sec + 0.1, min(end_sec, total_duration))

        start_frame = int(start_sec * framerate)
        end_frame = int(end_sec * framerate)
        frames_to_read = end_frame - start_frame

        win.setpos(start_frame)
        audio_data = win.readframes(frames_to_read)

    temp_out = target_out.with_suffix(".tmp.wav")
    with wave.open(str(temp_out), "wb") as wout:
        wout.setnchannels(nchannels)
        wout.setsampwidth(sampwidth)
        wout.setframerate(framerate)
        wout.writeframes(audio_data)

    if temp_out.exists():
        shutil.move(str(temp_out), str(target_out))

    return get_wav_duration(target_out)

def transcribe_clip_whisper(clip_path: Path) -> str:
    """Transcribes a specific audio clip using local Whisper."""
    python_exe = Path(r"C:\Users\rerun\AppData\Local\Programs\Python\Python312\python.exe")
    if not python_exe.exists():
        python_exe = Path(sys.executable)

    script = f"""
import whisper, sys
sys.stdout.reconfigure(encoding='utf-8')
m = whisper.load_model('base')
res = m.transcribe(r'{str(clip_path.resolve())}', language='ko')
print(res['text'].strip())
"""
    try:
        proc = subprocess.run(
            [str(python_exe), "-c", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30
        )
        lines = [l.strip() for l in proc.stdout.splitlines() if l.strip() and not l.startswith("C:\\") and "UserWarning" not in l]
        return " ".join(lines).strip()
    except Exception as e:
        print(f"[Curator] Whisper transcription error: {e}")
        return ""
