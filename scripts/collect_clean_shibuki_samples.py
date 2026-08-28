# -*- coding: utf-8 -*-
import os
import sys
import re
import subprocess
import tempfile
import shutil
from pathlib import Path

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(r"C:\Users\rerun\opendcmart\projects\project_buki")
WAV_OUTPUT_DIR = PROJECT_ROOT / "src" / "assets" / "voice_samples" / "shibuki"
LIST_FILE = WAV_OUTPUT_DIR / "shibuki.list"

TARGET_VIDEOS = [
    {
        "id": "msIPcAalaeI",
        "title": "휴가 다녀와서 잡담",
        "intervals": [(300, 600), (900, 1200), (1800, 2100)]
    },
    {
        "id": "jkzH7Jm-NSo",
        "title": "유메퍼센트 썰풀이 잡담",
        "intervals": [(400, 700), (1200, 1500)]
    },
    {
        "id": "sl2ipsuzJAk",
        "title": "2기 ppt 발표회 잡담",
        "intervals": [(600, 900), (1500, 1800)]
    }
]

def log(msg, symbol="🚀"):
    print(f"\n{symbol} {msg}", flush=True)

def run_cmd(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr

def download_and_extract_talk():
    os.makedirs(WAV_OUTPUT_DIR, exist_ok=True)
    temp_dir = Path(tempfile.gettempdir()) / "buki_voice_extraction"
    os.makedirs(temp_dir, exist_ok=True)

    existing_wavs = list(WAV_OUTPUT_DIR.glob("shibuki_sample_*.wav"))
    max_idx = 25
    for w in existing_wavs:
        m = re.search(r"shibuki_sample_(\d+)\.wav", w.name)
        if m:
            idx = int(m.group(1))
            if idx > max_idx:
                max_idx = idx

    current_idx = max_idx + 1
    log(f"Starting collection from sample index: {current_idx:03d}")

    import whisper
    log("Loading local Whisper model (base)...", "🧠")
    whisper_model = whisper.load_model("base")

    new_samples = []

    for vid in TARGET_VIDEOS:
        video_id = vid["id"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        log(f"Processing video: {vid['title']} ({video_id})", "📺")

        for start_sec, end_sec in vid["intervals"]:
            duration = end_sec - start_sec
            raw_mp3 = temp_dir / f"{video_id}_{start_sec}_{end_sec}.mp3"
            clean_wav = temp_dir / f"{video_id}_{start_sec}_{end_sec}_clean.wav"

            if not raw_mp3.exists():
                log(f"Downloading section {start_sec}s - {end_sec}s...")
                dl_cmd = f'python -m yt_dlp --extract-audio --audio-format mp3 --postprocessor-args "-ss {start_sec} -t {duration}" -o "{raw_mp3}" "{url}"'
                code, out, err = run_cmd(dl_cmd)
                if code != 0 or not raw_mp3.exists():
                    log(f"Failed to download slice: {err[:100]}", "⚠️")
                    continue

            dsp_cmd = (
                f'ffmpeg -y -i "{raw_mp3}" '
                f'-af "highpass=f=80,lowpass=f=12000,anlmdn=m=15:s=7,loudnorm=I=-20:TP=-1.5:LRA=11" '
                f'-ar 32000 -ac 1 -c:a pcm_s16le "{clean_wav}"'
            )
            code, out, err = run_cmd(dsp_cmd)
            if code != 0 or not clean_wav.exists():
                continue

            slice_pattern = str(temp_dir / f"clip_{video_id}_{start_sec}_%03d.wav")
            slice_cmd = (
                f'ffmpeg -y -i "{clean_wav}" '
                f'-af "silenceremove=start_periods=1:start_duration=0.2:start_threshold=-40dB:detection=peak,asetpts=N/SR/TB" '
                f'-f segment -segment_time 5.0 -c:a pcm_s16le "{slice_pattern}"'
            )
            run_cmd(slice_cmd)

            clips = sorted(temp_dir.glob(f"clip_{video_id}_{start_sec}_*.wav"))
            log(f"Generated {len(clips)} candidate voice clips.")

            for clip in clips:
                probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{clip}"'
                c, p_out, _ = run_cmd(probe_cmd)
                try:
                    dur = float(p_out.strip())
                except Exception:
                    dur = 0.0

                if dur < 3.0 or dur > 8.0:
                    clip.unlink(missing_ok=True)
                    continue

                result = whisper_model.transcribe(str(clip), language="ko", fp16=False)
                transcript = result.get("text", "").strip()
                transcript = re.sub(r"[^\w\s.,?!~]", "", transcript).strip()
                if len(transcript) < 4 or any(bad in transcript for bad in ["MBC", "뉴스", "시청해 주셔서", "구독과 좋아요", "감사합니다"]):
                    clip.unlink(missing_ok=True)
                    continue

                final_wav_name = f"shibuki_sample_{current_idx:03d}.wav"
                final_wav_path = WAV_OUTPUT_DIR / final_wav_name
                shutil.copy2(str(clip), str(final_wav_path))

                line = f"{final_wav_path.as_posix()}|shibuki|ko|{transcript}"
                new_samples.append(line)
                log(f"  [+] #{current_idx:03d} ({dur:.2f}s): {transcript}", "✨")
                current_idx += 1

                clip.unlink(missing_ok=True)

                if len(new_samples) >= 30:
                    break
            if len(new_samples) >= 30:
                break
        if len(new_samples) >= 30:
            break

    if new_samples:
        log(f"Appending {len(new_samples)} clean verified samples to shibuki.list...", "📝")
        with open(LIST_FILE, "a", encoding="utf-8") as f:
            for line in new_samples:
                f.write(line + "\n")
        log(f"Successfully expanded shibuki.list! Total new samples: {len(new_samples)}", "🎉")
    else:
        log("No new valid samples found.", "⚠️")

if __name__ == "__main__":
    download_and_extract_talk()
