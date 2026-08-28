import os
import sys
import glob
from pathlib import Path
import yt_dlp
from yt_dlp.utils import download_range_func

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

scratch_dir = Path("C:/Users/rerun/opendcmart/projects/project_buki/scratch_voice_extract")
scratch_dir.mkdir(parents=True, exist_ok=True)

vids = [
    ("msIPcAalaeI", 300.0, 750.0), # 5m ~ 12.5m (450s = 7.5m)
    ("jkzH7Jm-NSo", 300.0, 750.0)  # 5m ~ 12.5m (450s = 7.5m)
]

for vid, start_s, end_s in vids:
    target_wav = scratch_dir / f"{vid}_talk.wav"
    if target_wav.exists() and target_wav.stat().st_size > 1000000:
        print(f"[+] {target_wav.name} already exists ({target_wav.stat().st_size / 1024 / 1024:.2f} MB)")
        continue

    url = f"https://www.youtube.com/watch?v={vid}"
    outtmpl = str(scratch_dir / f"{vid}_talk.%(ext)s")
    
    print(f"[*] Downloading [{start_s}s ~ {end_s}s] from {url}...")
    ydl_opts = {
        'format': '140/18/bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': outtmpl,
        'download_ranges': download_range_func(None, [(start_s, end_s)]),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': False,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find generated wav
    matches = list(scratch_dir.glob(f"{vid}_talk*.wav"))
    print(f"[+] Matches for {vid}:", [m.name for m in matches])
    if matches and not target_wav.exists():
        matches[0].rename(target_wav)
        print(f"[+] Renamed {matches[0].name} -> {target_wav.name}")

print("\n--- Current files in scratch_voice_extract ---")
for p in scratch_dir.iterdir():
    print(f"  {p.name} ({p.stat().st_size if p.is_file() else 'dir'})")
