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
