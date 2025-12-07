# File: clipper.py
import os
import subprocess


def split_video_ffmpeg(input_path, clip_length=60):
    filename = os.path.basename(input_path)

    if filename == "fart.mp4":
        output_folder = "gameplay"
    elif filename == "podcast.mp4":
        output_folder = "podcast_output"
    else:
        output_folder = "clips_output"

    os.makedirs(output_folder, exist_ok=True)
    output_pattern = os.path.join(output_folder, "%d.mp4")

    command = [
        "ffmpeg",
        "-i", input_path,
        "-c", "copy",
        "-map", "0",
        "-f", "segment",
        "-segment_time", str(clip_length),
        "-reset_timestamps", "1",
        output_pattern
    ]

    print("Running command:", " ".join(command))
    subprocess.run(command, check=True)
    print(f"Clips saved in {output_folder}")


def extract_clip_by_timestamp(input_path, start_seconds, duration_seconds, output_path):
    """Extract a specific time range from a video.
    
    Args:
        input_path: Path to input video
        start_seconds: Start time in seconds (can be float)
        duration_seconds: Duration in seconds (can be float)
        output_path: Path for output clip
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    # Format time for ffmpeg (HH:MM:SS.mmm)
    def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
    
    start_time = format_time(start_seconds)
    
    # Using -c copy for speed. For frame-accurate cuts, remove -c copy and add re-encoding
    command = [
        "ffmpeg",
        "-i", input_path,
        "-ss", start_time,
        "-t", str(duration_seconds),
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        "-y",
        output_path
    ]
    
    print(f"Extracting clip: {start_time} for {duration_seconds}s -> {os.path.basename(output_path)}")
    subprocess.run(command, check=True, capture_output=True)
    print(f"Saved clip: {output_path}")
