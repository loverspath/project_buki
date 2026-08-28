#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
Project BUKI - 100% Pure Clean Shibuki Voice Dataset Expansion & Purification
==============================================================================
Target Archives:
  - msIPcAalaeI (휴가 다녀와서 잡담)
  - sl2ipsuzJAk (2기 ppt 발표회 잡담)
  - jkzH7Jm-NSo (유메퍼센트 썰풀이/잡담 구간)
  - dKNSz5UtAEY (2026.08.26 잡담 구간)

Strict Quality Pipeline:
  1. Download clean talk audio slices via yt-dlp.
  2. Apply 5-stage FFmpeg DSP vocal isolation filter chain (afftdn, bandpass 80Hz~12kHz, presence EQ, speechnorm).
  3. Silence detection & VAD precision slicing to 3.0s ~ 7.0s segments.
  4. Audio standardization: 32kHz 16-bit Mono PCM WAV, -20 LUFS normalized with fade-in/out.
  5. Gemini 3.6 Flash multimodal transcription & strict noise/donation/BGM detection.
  6. Filter & accept only 100% clean samples.
  7. Save as shibuki_sample_026.wav onwards, update shibuki.list, voice_manifest.json, sample_registry.json.
==============================================================================
"""

import os
import sys
import json
import re
import time
import shutil
import base64
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
import httpx
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ENV_PATH = Path("C:/Users/rerun/opendcmart/projects/project_buki/.env")
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
BASE_DIR = Path("C:/Users/rerun/opendcmart/projects/project_buki")
TARGET_DIR = BASE_DIR / "src" / "assets" / "voice_samples" / "shibuki"
REGISTRY_FILE = BASE_DIR / "src" / "assets" / "voice_samples" / "sample_registry.json"
MANIFEST_FILE = TARGET_DIR / "voice_manifest.json"
LIST_FILE = TARGET_DIR / "shibuki.list"
REPORT_FILE = TARGET_DIR / "EXTRACTION_REPORT.md"
SCRATCH_DIR = BASE_DIR / "scratch_voice_extract"

TARGET_SR = 32000
TARGET_LUFS = -20.0
MIN_DUR = 3.0
MAX_DUR = 7.0
TARGET_TOTAL_CLEAN = 40  # 9 existing + 31 new = 40 clean samples


def run_cmd(cmd: List[str], desc: str = "") -> str:
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print(f"  [ERROR] {desc} (code {res.returncode}): {res.stderr[-300:]}")
        raise RuntimeError(f"Command failed: {desc}")
    return res.stdout


def download_archive_slices():
    """Downloads candidate Just Chatting sections from the 4 YouTube archives."""
    import yt_dlp
    from yt_dlp.utils import download_range_func

    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

    # 4 Target archives and rich Just Chatting time slices
    targets = [
        ("msIPcAalaeI", 600.0, 1200.0, "msIPcAalaeI_talk1.wav"),
        ("sl2ipsuzJAk", 600.0, 1200.0, "sl2ipsuzJAk_talk1.wav"),
        ("jkzH7Jm-NSo", 600.0, 1200.0, "jkzH7Jm_talk1.wav"),
        ("jkzH7Jm-NSo", 18000.0, 18600.0, "jkzH7Jm_talk2.wav"),
        ("dKNSz5UtAEY", 600.0, 1200.0, "dKNSz5UtAEY_talk1.wav"),
    ]

    print("\n" + "=" * 70)
    print(" 📥 Stage 1: Downloading Just Chatting Talk Slices from 4 YouTube Archives")
    print("=" * 70)

    downloaded = []
    for vid, st, et, out_name in targets:
        dest_path = SCRATCH_DIR / out_name
        if dest_path.exists() and dest_path.stat().st_size > 500000:
            print(f"  [+] Found cached source file: {out_name} ({dest_path.stat().st_size / 1024 / 1024:.2f} MB)")
            downloaded.append((dest_path, vid, st, et))
            continue

        url = f"https://www.youtube.com/watch?v={vid}"
        print(f"  [*] Downloading [{st:.0f}s ~ {et:.0f}s] from {vid} -> {out_name}...")

        ydl_opts = {
            'format': '18/140/bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(SCRATCH_DIR / f"{vid}_{st:.0f}_temp.%(ext)s"),
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'download_ranges': download_range_func(None, [(st, et)]),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            matches = list(SCRATCH_DIR.glob(f"{vid}_{st:.0f}_temp*.wav"))
            if matches:
                if dest_path.exists():
                    dest_path.unlink()
                matches[0].rename(dest_path)
                print(f"  [✓] Downloaded and saved: {dest_path.name} ({dest_path.stat().st_size / 1024 / 1024:.2f} MB)")
                downloaded.append((dest_path, vid, st, et))
        except Exception as e:
            print(f"  [!] Failed downloading {vid} [{st}~{et}]: {e}")

    return downloaded


def apply_dsp_filters(input_wav: Path, output_wav: Path):
    """Applies FFmpeg 5-stage DSP vocal cleanup chain."""
    dsp_filter = (
        "highpass=f=80,lowpass=f=12000,"
        "afftdn=nf=-22:tn=1,"
        "equalizer=f=2500:t=q:w=1.2:g=2.5,"
        "speechnorm=e=4:r=0.0001:l=1"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(input_wav),
        "-af", dsp_filter,
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "1",
        str(output_wav)
    ]
    run_cmd(cmd, desc="FFmpeg DSP Vocal Cleanup")


def detect_silences(audio_path: Path) -> List[Dict[str, float]]:
    cmd = [
        "ffmpeg", "-i", str(audio_path),
        "-af", "silencedetect=noise=-28dB:d=0.35",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    starts = []
    ends = []
    for line in res.stderr.splitlines():
        if "silence_start:" in line:
            m = re.search(r"silence_start:\s*([0-9.]+)", line)
            if m:
                starts.append(float(m.group(1)))
        elif "silence_end:" in line:
            m = re.search(r"silence_end:\s*([0-9.]+)", line)
            if m:
                ends.append(float(m.group(1)))

    silences = []
    for s, e in zip(starts, ends):
        if e > s:
            silences.append({"start": s, "end": e})
    return silences


def get_speech_intervals(audio_path: Path, min_dur: float = 3.0, max_dur: float = 7.0) -> List[Tuple[float, float]]:
    probe_cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)]
    total_dur = float(subprocess.run(probe_cmd, stdout=subprocess.PIPE, text=True, check=True).stdout.strip() or 0.0)

    silences = detect_silences(audio_path)
    raw_speeches = []
    last_end = 0.0
    for s in silences:
        if s["start"] > last_end + 0.2:
            raw_speeches.append((last_end, s["start"]))
        last_end = s["end"]
    if total_dur > last_end + 0.2:
        raw_speeches.append((last_end, total_dur))

    refined = []
    i = 0
    while i < len(raw_speeches):
        st, et = raw_speeches[i]
        dur = et - st
        while dur < min_dur and i + 1 < len(raw_speeches):
            next_st, next_et = raw_speeches[i+1]
            if next_st - et < 0.5 and (next_et - st) <= max_dur:
                et = next_et
                dur = et - st
                i += 1
            else:
                break

        if min_dur <= dur <= max_dur:
            refined.append((st, et))
        elif dur > max_dur:
            sub_cur = st
            while sub_cur + min_dur <= et:
                sub_end = min(et, sub_cur + 5.5)
                refined.append((sub_cur, sub_end))
                sub_cur += 5.0
        i += 1

    return refined


def standardize_clip(src_wav: Path, st: float, et: float, out_wav: Path):
    dur = et - st
    audio_filter = f"afade=t=in:st=0:d=0.03,afade=t=out:st={dur-0.03:.3f}:d=0.03,loudnorm=I={TARGET_LUFS}:LRA=11:TP=-1.5"
    cmd = [
        "ffmpeg", "-y", "-ss", f"{st:.3f}", "-to", f"{et:.3f}",
        "-i", str(src_wav),
        "-af", audio_filter,
        "-ar", str(TARGET_SR), "-ac", "1", "-c:a", "pcm_s16le",
        str(out_wav)
    ]
    run_cmd(cmd, desc=f"Standardize {out_wav.name}")


def gemini_stt_classify(wav_path: Path) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    with open(wav_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = (
        "You are an expert audio quality analyzer and phonetic transcriber for VTuber voice cloning.\n"
        "Analyze this Korean speech audio clip of Tenko Shibuki (텐코 시부키).\n\n"
        "Strict Quality Criteria:\n"
        "1. Transcribe the spoken words verbatim in Korean with 100% precision. Do NOT translate or hallucinate. Keep Korean filler words (어, 그, 막, 아, 근데, 하하).\n"
        "2. Emotion tone: Choose ONE of ['neutral', 'smug', 'tease', 'angry', 'whisper', 'sensual', 'flustered', 'resigned'].\n"
        "3. Detect background noises:\n"
        "   - has_donation_sound: true if there is any donation alert, chime, bell, ding-dong, fanfare, or TTS donation voice.\n"
        "   - has_bgm_or_song: true if there is loud background music or singing.\n"
        "   - has_rustling_or_bumps: true if there is plastic bag rustling, mic bumps, or heavy banging.\n"
        "   - is_clean: true ONLY if speech is clear without donation sounds, rustling, or loud overlap.\n\n"
        "Output JSON only:\n"
        "{\n"
        '  "transcript": "<exact Korean speech>",\n'
        '  "emotion": "<emotion>",\n'
        '  "has_donation_sound": false,\n'
        '  "has_bgm_or_song": false,\n'
        '  "has_rustling_or_bumps": false,\n'
        '  "is_clean": true,\n'
        '  "confidence": 0.95\n'
        "}"
    )

    models_to_try = ["gemini-3.6-flash", "gemini-flash-latest"]
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "audio/wav", "data": audio_b64}}
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }
        for attempt in range(3):
            try:
                res = httpx.post(url, json=payload, timeout=25.0)
                if res.status_code == 200:
                    res_json = res.json()
                    candidates = res_json.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                        if raw_text.startswith("```json"):
                            raw_text = raw_text[7:]
                        elif raw_text.startswith("```"):
                            raw_text = raw_text[3:]
                        if raw_text.endswith("```"):
                            raw_text = raw_text[:-3]
                        raw_text = raw_text.strip()
                        return json.loads(raw_text)
                elif res.status_code == 429:
                    print(f"  [429 Rate Limit on {model_name}] Waiting 6s...")
                    time.sleep(6.0)
                    continue
                else:
                    break
            except Exception as e:
                time.sleep(1.5)

    return {
        "transcript": "",
        "emotion": "neutral",
        "has_donation_sound": True,
        "has_bgm_or_song": True,
        "has_rustling_or_bumps": True,
        "is_clean": False,
        "confidence": 0.0
    }


def main():
    print("=" * 75)
    print(" 🦊 Shibuki 100% Pure Voice Dataset Expansion & Fine-Tuning Pipeline")
    print("=" * 75)

    # 1. Download source slices
    downloaded_sources = download_archive_slices()

    # 2. Apply DSP and slice
    print("\n" + "=" * 70)
    print(" 🧹 Stage 2: 5-Stage DSP Vocal Isolation & VAD Interval Slicing")
    print("=" * 70)

    temp_dsp_dir = SCRATCH_DIR / "dsp_cleaned"
    temp_dsp_dir.mkdir(parents=True, exist_ok=True)
    temp_clips_dir = SCRATCH_DIR / "raw_candidate_clips"
    temp_clips_dir.mkdir(parents=True, exist_ok=True)

    candidate_clips = []
    for src_file, vid, base_st, base_et in downloaded_sources:
        if not src_file.exists():
            continue
        cleaned_wav = temp_dsp_dir / f"{src_file.stem}_dsp.wav"
        apply_dsp_filters(src_file, cleaned_wav)

        intervals = get_speech_intervals(cleaned_wav, min_dur=MIN_DUR, max_dur=MAX_DUR)
        print(f"  [+] {src_file.name}: Extracted {len(intervals)} speech intervals")

        for idx, (st, et) in enumerate(intervals):
            dur = et - st
            clip_file = temp_clips_dir / f"{src_file.stem}_clip_{idx:03d}.wav"
            standardize_clip(cleaned_wav, st, et, clip_file)
            candidate_clips.append((clip_file, dur, vid, base_st + st, base_st + et))

    print(f"\n[+] Total candidate standardized audio clips generated: {len(candidate_clips)}")

    # 3. Existing 9 clean samples
    clean_original_indices = [10, 11, 12, 13, 14, 15, 17, 19, 23]
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        existing_manifest = json.load(f)

    existing_samples_dict = {s["index"]: s for s in existing_manifest.get("samples", [])}
    clean_base_samples = [existing_samples_dict[idx] for idx in clean_original_indices if idx in existing_samples_dict]
    print(f"[+] Loaded {len(clean_base_samples)} verified clean base samples from original dataset.")

    # 4. Multimodal STT & Strict Quality Filter
    print("\n" + "=" * 70)
    print(" 🎙️ Stage 3: Gemini 3.6 Flash Multimodal Audio STT & 100% Clean Filtering")
    print("=" * 70)

    needed_new_count = TARGET_TOTAL_CLEAN - len(clean_base_samples)
    print(f"[*] Target: Extract {needed_new_count} additional clean samples (starting at 026)...")

    accepted_new_samples = []
    next_sample_index = 26

    for clip_file, dur, vid, abs_st, abs_et in candidate_clips:
        if len(accepted_new_samples) >= needed_new_count:
            break

        try:
            analysis = gemini_stt_classify(clip_file)
            time.sleep(1.5)  # Respect rate limits

            transcript = analysis.get("transcript", "").strip()
            emotion = analysis.get("emotion", "neutral").lower()
            conf = float(analysis.get("confidence", 0.0))
            is_clean = bool(analysis.get("is_clean", False))
            has_don = bool(analysis.get("has_donation_sound", False))
            has_bgm = bool(analysis.get("has_bgm_or_song", False))
            has_rustle = bool(analysis.get("has_rustling_or_bumps", False))

            # Quality Check:
            # - Must be marked is_clean
            # - No donation sounds, no BGM/song, no rustling/bumps
            # - Confidence >= 0.88
            # - Transcript length >= 7 chars
            # - No markdown/code fences
            if not is_clean or has_don or has_bgm or has_rustle:
                print(f"  [-] Rejected {clip_file.name}: noisy (clean={is_clean}, don={has_don}, bgm={has_bgm}, rustle={has_rustle})")
                continue
            if conf < 0.88 or len(transcript) < 7:
                print(f"  [-] Rejected {clip_file.name}: low conf ({conf:.2f}) or short text ('{transcript}')")
                continue

            sample_id = f"shibuki_sample_{next_sample_index:03d}"
            final_wav = TARGET_DIR / f"{sample_id}.wav"
            shutil.copyfile(clip_file, final_wav)

            sample_entry = {
                "index": next_sample_index,
                "sample_id": sample_id,
                "file_path": str(final_wav).replace("\\", "/"),
                "duration": round(dur, 2),
                "emotion": emotion,
                "transcript": transcript,
                "confidence": conf,
                "source_archive": vid,
                "archive_time": f"{abs_st:.1f}s ~ {abs_et:.1f}s"
            }
            accepted_new_samples.append(sample_entry)
            print(f"  [✓] Accepted {sample_id} ({dur:.2f}s | {emotion} | {conf:.2f}): \"{transcript}\"")
            next_sample_index += 1

        except Exception as e:
            print(f"  [!] Error evaluating {clip_file.name}: {e}")

    print(f"\n[+] Successfully collected {len(accepted_new_samples)} new clean samples!")

    # 5. Build Master Clean Dataset (Base 9 + New Samples)
    master_samples = clean_base_samples + accepted_new_samples
    print(f"[+] Total Master Clean Dataset Size: {len(master_samples)} samples")

    # 6. Update voice_manifest.json
    emotion_banks = {
        "smug": {
            "ref_wav": "C:/Users/rerun/opendcmart/projects/project_buki/src/assets/voice_samples/shibuki/shibuki_sample_014.wav",
            "prompt_text": "대박 대박 대박 구했습니다! 하하!",
            "lang": "ko"
        },
        "tease": {
            "ref_wav": "C:/Users/rerun/opendcmart/projects/project_buki/src/assets/voice_samples/shibuki/shibuki_sample_010.wav",
            "prompt_text": "여러분, 밤을 주웠어요. 상상도 못했죠?",
            "lang": "ko"
        },
        "flustered": {
            "ref_wav": "C:/Users/rerun/opendcmart/projects/project_buki/src/assets/voice_samples/shibuki/shibuki_sample_013.wav",
            "prompt_text": "하아! 밍 감사합니다. 고맙습니다. 아 익명의 후원자님이 10만 친즈 공...",
            "lang": "ko"
        },
        "neutral": {
            "ref_wav": "C:/Users/rerun/opendcmart/projects/project_buki/src/assets/voice_samples/shibuki/shibuki_sample_011.wav",
            "prompt_text": "구독 기념 인사가 되게 많아서 좀 밀렸나? 아이 구독 감사합니다. 고맙습니다. 2개월",
            "lang": "ko"
        }
    }

    # Add any newly discovered emotions
    for s in accepted_new_samples:
        emo = s["emotion"]
        if emo not in emotion_banks:
            emotion_banks[emo] = {
                "ref_wav": s["file_path"],
                "prompt_text": s["transcript"],
                "lang": "ko"
            }

    manifest_output = {
        "persona_id": "shibuki",
        "persona_name": "텐코 시부키 (Tenko Shibuki)",
        "target_lang": "ko",
        "total_samples": len(master_samples),
        "clean_only": True,
        "registry_config": {
            "default_ref_wav": emotion_banks["smug"]["ref_wav"],
            "default_prompt_text": emotion_banks["smug"]["prompt_text"],
            "prompt_lang": "ko",
            "target_lang": "ko",
            "emotion_banks": emotion_banks
        },
        "samples": master_samples
    }

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest_output, f, ensure_ascii=False, indent=2)
    print(f"[✓] Updated {MANIFEST_FILE}")

    # 7. Update shibuki.list (for GPT-SoVITS Fine-Tuning)
    with open(LIST_FILE, "w", encoding="utf-8") as f:
        for s in master_samples:
            f.write(f"{s['file_path']}|shibuki|ko|{s['transcript']}\n")
    print(f"[✓] Updated {LIST_FILE} ({len(master_samples)} lines)")

    # 8. Update sample_registry.json
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        registry = json.load(f)

    registry["shibuki"] = {
        "default_ref_wav": emotion_banks["smug"]["ref_wav"],
        "default_prompt_text": emotion_banks["smug"]["prompt_text"],
        "prompt_lang": "ko",
        "target_lang": "ko",
        "emotion_banks": emotion_banks
    }

    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print(f"[✓] Updated {REGISTRY_FILE}")

    # 9. Update EXTRACTION_REPORT.md
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# 🎙️ Tenko Shibuki 100% Pure Voice Dataset & Fine-Tuning Report\n\n")
        f.write(f"- **Persona ID**: `shibuki`\n")
        f.write(f"- **Language**: `ko` (Korean)\n")
        f.write(f"- **Total Clean Samples**: {len(master_samples)} (9 verified base + {len(accepted_new_samples)} newly extracted)\n")
        f.write(f"- **Target Replay Archives**:\n")
        f.write(f"  - `msIPcAalaeI` (휴가 다녀와서 잡담)\n")
        f.write(f"  - `sl2ipsuzJAk` (2기 ppt 발표회 잡담)\n")
        f.write(f"  - `jkzH7Jm-NSo` (유메퍼센트 썰풀이/잡담 구간)\n")
        f.write(f"  - `dKNSz5UtAEY` (2026.08.26 잡담 구간)\n")
        f.write(f"- **Audio Standard**: 32,000Hz 16-bit Mono PCM WAV, -20.0 LUFS Normalized\n")
        f.write(f"- **Purification Criteria**: 100% Zero-Donation, Zero-BGM, Zero-Rustle, Gemini 3.6 Flash Verified\n\n")

        f.write("## 🌟 Active Emotion Banks\n\n")
        f.write("| Emotion | Reference File | Prompt Text |\n")
        f.write("| :--- | :--- | :--- |\n")
        for emo, val in emotion_banks.items():
            ref_basename = Path(val['ref_wav']).name
            f.write(f"| **{emo.upper()}** | `{ref_basename}` | {val['prompt_text']} |\n")

        f.write("\n## 📋 Master Dataset Sample Registry\n\n")
        f.write("| # | Sample ID | Emotion | Duration | Spoken Transcript | Archive / Confidence |\n")
        f.write("| :---: | :--- | :---: | :---: | :--- | :---: |\n")
        for s in master_samples:
            src_info = s.get("source_archive", "base_clean")
            conf_info = f"{s.get('confidence', 0.95):.2f}"
            f.write(f"| {s['index']} | `{s['sample_id']}` | `{s['emotion']}` | {s['duration']}s | {s['transcript']} | {src_info} ({conf_info}) |\n")

    print(f"[✓] Generated extraction report: {REPORT_FILE}")
    print("\n🎉 Stage 1~3 Complete! Dataset is ready for GPT-SoVITS Fine-Tuning!")


if __name__ == "__main__":
    main()
