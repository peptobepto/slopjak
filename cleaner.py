# File: cleaner.py
import os
import json


def cleanup_and_rename_clips(json_file="clip_ratings.json", video_folder="podcast_output", subtitle_folder="subtitles", top_n=5):
    with open(json_file, "r", encoding="utf-8") as f:
        clips = json.load(f)

    clips_sorted = sorted([c for c in clips if c.get("rating") is not None], key=lambda x: x["rating"], reverse=True)
    top_clips = clips_sorted[:top_n]

    top_clip_filenames = set(c["clip"].replace(".srt", ".mp4") for c in top_clips)
    print(f"Top {top_n} clips to keep: {[c['clip'] for c in top_clips]}")

    # Delete video files not in top clips
    for file in os.listdir(video_folder):
        if file.endswith(".mp4") and file not in top_clip_filenames:
            os.remove(os.path.join(video_folder, file))
            print(f"Deleted video: {file}")

    # Delete subtitle files not in top clips
    for file in os.listdir(subtitle_folder):
        if file.endswith(".srt") and file.replace(".srt", ".mp4") not in top_clip_filenames:
            os.remove(os.path.join(subtitle_folder, file))
            print(f"Deleted subtitle: {file}")

    # Rename remaining top clips safely using temporary names
    temp_map = {}
    for i, clip in enumerate(top_clips, start=1):
        old_video_path = os.path.join(video_folder, clip["clip"].replace(".srt", ".mp4"))
        temp_video_path = os.path.join(video_folder, f"tmp_{i}.mp4")
        os.rename(old_video_path, temp_video_path)
        temp_map[temp_video_path] = os.path.join(video_folder, f"{i}.mp4")

        old_srt_path = os.path.join(subtitle_folder, clip["clip"])
        temp_srt_path = os.path.join(subtitle_folder, f"tmp_{i}.srt")
        os.rename(old_srt_path, temp_srt_path)
        temp_map[temp_srt_path] = os.path.join(subtitle_folder, f"{i}.srt")

    for temp_path, final_path in temp_map.items():
        os.rename(temp_path, final_path)
        print(f"Renamed {temp_path} -> {final_path}")
