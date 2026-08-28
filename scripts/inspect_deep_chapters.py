import sys
import json
import yt_dlp

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

vids = ['msIPcAalaeI', 'sl2ipsuzJAk', 'jkzH7Jm-NSo', 'dKNSz5UtAEY']
ydl_opts = {'quiet': True, 'extract_flat': False}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    for vid in vids:
        url = f"https://www.youtube.com/watch?v={vid}"
        info = ydl.extract_info(url, download=False)
        print(f"\n=======================================================")
        print(f"Video ID: {vid}")
        print(f"Title: {info.get('title')}")
        print(f"Duration: {info.get('duration')}s ({float(info.get('duration',0))/60:.1f}m)")
        print(f"Chapters count: {len(info.get('chapters') or [])}")
        for ch in info.get('chapters') or []:
            st = ch.get('start_time', 0)
            et = ch.get('end_time', 0)
            print(f"  Chapter: [{st//60:02.0f}:{st%60:02.0f} ({st}s) ~ {et//60:02.0f}:{et%60:02.0f} ({et}s)] {ch.get('title')}")
        print("Description:")
        for l in (info.get('description') or '').splitlines():
            if l.strip():
                print(f"  {l}")
