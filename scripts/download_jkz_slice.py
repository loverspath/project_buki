import os
import sys
import yt_dlp
from yt_dlp.utils import download_range_func
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

scratch_dir = Path("C:/Users/rerun/opendcmart/projects/project_buki/scratch_voice_extract")
scratch_dir.mkdir(parents=True, exist_ok=True)

url = "https://www.youtube.com/watch?v=jkzH7Jm-NSo"
out_tmpl = str(scratch_dir / "jkzH7Jm_talk.%(ext)s")

ydl_opts = {
    'format': '140/18/bestaudio[ext=m4a]/bestaudio/best',
    'outtmpl': out_tmpl,
    'download_ranges': download_range_func(None, [(300.0, 720.0)]), # 5m ~ 12m
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192',
    }],
    'quiet': False,
    'no_warnings': True,
}

print(f"Downloading talk window [300s ~ 720s] from {url}...")
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])

wav_files = list(scratch_dir.glob("jkzH7Jm_talk*.wav"))
print("Downloaded WAV files:", [str(w) for w in wav_files])
