import sys
import json
import yt_dlp

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ydl_opts = {
    'quiet': True,
    'extract_flat': True,
    'playlist_items': '1-10'
}

print("Fetching videos from @shibukireplay/videos...")
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    res = ydl.extract_info('https://www.youtube.com/@shibukireplay/videos', download=False)
    entries = res.get('entries', [])
    print(f"Found {len(entries)} videos:")
    for e in entries:
        vid = e.get('id')
        title = e.get('title')
        dur = e.get('duration')
        print(f"  ID: {vid} | Duration: {dur}s | Title: {title}")
