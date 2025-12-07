# File: combiner.py
import os
import random
import subprocess


def combine_portrait(podcast_folder="podcast_output", gameplay_folder="gameplay", output_folder="combined"):
    os.makedirs(output_folder, exist_ok=True)

    podcast_clips = sorted([f for f in os.listdir(podcast_folder) if f.endswith(".mp4")])
    gameplay_clips = sorted([f for f in os.listdir(gameplay_folder) if f.endswith(".mp4")])

    if not gameplay_clips:
        print("No gameplay clips found to combine; skipping.")
        return

    for clip_name in podcast_clips:
        podcast_path = os.path.join(podcast_folder, clip_name)
        gameplay_clip = random.choice(gameplay_clips)
        gameplay_path = os.path.join(gameplay_folder, gameplay_clip)

        temp_output = os.path.join(output_folder, f"temp_{clip_name}")
        final_output = os.path.join(output_folder, clip_name)

        print(f"Combining {podcast_path} with {gameplay_path} -> {temp_output}")

        stack_cmd = [
            "ffmpeg",
            "-y",
            "-i", podcast_path,
            "-i", gameplay_path,
            "-filter_complex",
            "[0:v]fps=30,scale=720:-2,setsar=1[top];"
            "[1:v]fps=30,scale=720:-2,setsar=1[bottom];"
            "[top][bottom]vstack=inputs=2[stacked]",
            "-map", "[stacked]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            temp_output
        ]
        try:
            subprocess.run(stack_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error stacking {clip_name} with {gameplay_clip}: {e}")
            continue

        # Crop the stacked video to 9:16 portrait
        def crop_to_portrait_ffmpeg(input_file, output_file):
            cmd_probe = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0:s=x",
                input_file
            ]
            result = subprocess.run(cmd_probe, capture_output=True, text=True)
            width, height = map(int, result.stdout.strip().split('x'))

            target_aspect = 9 / 16
            input_aspect = width / height

            if input_aspect > target_aspect:
                new_width = int(height * target_aspect)
                new_height = height
                x_offset = (width - new_width) // 2
                y_offset = 0
            else:
                new_width = width
                new_height = int(width / target_aspect)
                x_offset = 0
                y_offset = (height - new_height) // 2

            crop_filter = f"crop={new_width}:{new_height}:{x_offset}:{y_offset}"

            crop_cmd = [
                "ffmpeg", "-y", "-i", input_file,
                "-vf", crop_filter,
                "-c:a", "copy",
                output_file
            ]
            subprocess.run(crop_cmd, check=True)

        crop_to_portrait_ffmpeg(temp_output, final_output)
        try:
            os.remove(temp_output)
        except Exception:
            pass
        print(f"Final portrait video saved as: {final_output}")





