import os
import uuid
import random
import pysrt
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.config as mp_config

# ImageMagick path
IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
mp_config.change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})

def burn_all_subtitles(combined_folder="combined",
                       subtitles_folder="subtitles",
                       output_folder="final_with_subs",
                       fontsize=50,
                       font="Impact",
                       color="#FFFFFF",
                       highlight_color="#00FF00",
                       stroke_color="black",
                       stroke_width=2,
                       fps=30,
                       max_height_ratio=0.25,
                       highlight_prob=0.2,
                       bounce_height=30,
                       bounce_duration=0.3):
    os.makedirs(output_folder, exist_ok=True)

    for file in sorted(os.listdir(combined_folder)):
        if not file.endswith(".mp4"):
            continue

        base = file.replace(".mp4", "")
        video_path = os.path.join(combined_folder, file)
        srt_path = os.path.join(subtitles_folder, f"{base}.srt")

        if not os.path.exists(srt_path):
            print(f"No matching subtitles for {file}, skipping.")
            continue

        random_name = uuid.uuid4().hex[:8]
        output_path = os.path.join(output_folder, f"{random_name}.mp4")

        print(f"Adding subtitles to {file} -> {random_name}.mp4")

        video = VideoFileClip(video_path)
        subs = pysrt.open(srt_path)
        subtitle_clips = []

        for sub in subs:
            txt = sub.text.strip().replace("\n", " ").upper()
            words = txt.split()
            if not words:
                continue

            start = sub.start.ordinal / 1000.0
            end = sub.end.ordinal / 1000.0
            if end <= start:
                continue

            # create TextClips per word, randomly highlight
            word_clips = []
            for word in words:
                color_choice = highlight_color if random.random() < highlight_prob else color
                word_clip = TextClip(
                    word,
                    fontsize=fontsize,
                    font=font,
                    color=color_choice,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    method="caption"
                )
                word_clips.append(word_clip)

            # combine words into a single line, horizontally spaced
            total_width = sum(w.w for w in word_clips)
            x_cursor = (video.w - total_width) // 2

            for w in word_clips:
                # bounce position function
                def make_position(t, x=x_cursor, start_time=start, end_time=end):
                    y_center = video.h // 2
                    if start_time <= t <= start_time + bounce_duration:
                        progress = (t - start_time) / bounce_duration
                        y = y_center - bounce_height * (1 - (progress - 1)**2)  # smooth parabola
                    else:
                        y = y_center
                    return (x, y)

                w = w.set_start(start).set_end(end).set_position(make_position)
                subtitle_clips.append(w)
                x_cursor += w.w

        final = CompositeVideoClip([video, *subtitle_clips])
        final.write_videofile(output_path,
                              codec="libx264",
                              audio_codec="aac",
                              fps=fps)
