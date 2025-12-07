# File: downloader.py
import yt_dlp
import os


def download_video(url, filename):
    """Download a video from YouTube using yt-dlp.
    
    Args:
        url: YouTube URL (or any URL supported by yt-dlp)
        filename: Output filename (will be saved in current directory)
    """
    # Ensure filename has .mp4 extension
    if not filename.endswith('.mp4'):
        filename = filename + '.mp4'
    
    ydl_opts = {
        "outtmpl": filename,
        # More flexible format selection - will fallback to best available
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": False,  # Show progress
        "no_warnings": False,
    }
    
    try:
        print(f"Downloading video from: {url}")
        print(f"Output file: {filename}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Verify file was created
        if os.path.exists(filename):
            file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
            print(f"✓ Successfully downloaded: {filename} ({file_size:.2f} MB)")
            return filename
        else:
            print(f"✗ Error: File {filename} was not created")
            return None
    except Exception as e:
        print(f"✗ Error downloading video: {e}")
        print("Make sure the URL is valid and yt-dlp is up to date (pip install --upgrade yt-dlp)")
        raise


