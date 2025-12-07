# File: downloader.py
import yt_dlp


def download_video(url, filename):
    ydl_opts = {
        "outtmpl": filename,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


