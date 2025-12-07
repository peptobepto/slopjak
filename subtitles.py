import os
import uuid
import random
import shutil
import pysrt
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from tqdm import tqdm
from PIL import ImageFont

# ImageMagick path - auto-detect for Linux
# MoviePy 2.x auto-detects ImageMagick, but we can set it via environment variable if needed
IMAGEMAGICK_BINARY = shutil.which("magick") or shutil.which("convert") or "convert"
if IMAGEMAGICK_BINARY and IMAGEMAGICK_BINARY != "convert":
    # Set environment variable for ImageMagick (MoviePy 2.x uses this)
    os.environ["IMAGEMAGICK_BINARY"] = IMAGEMAGICK_BINARY


def find_available_font(preferred_fonts):
    """Try to find an available font from a list of preferred fonts.
    Prioritizes bold, YouTube-friendly fonts.
    
    Args:
        preferred_fonts: List of font names to try in order
        
    Returns:
        Font name that works, or None if none found
    """
    for font_name in preferred_fonts:
        try:
            # Try to load the font
            test_font = ImageFont.truetype(font_name, size=20)
            return font_name
        except (OSError, IOError):
            # Try common system font paths
            common_paths = [
                f"/usr/share/fonts/truetype/{font_name.lower()}.ttf",
                f"/usr/share/fonts/truetype/{font_name.lower()}/{font_name}-Regular.ttf",
                f"/usr/share/fonts/TTF/{font_name}.ttf",
                f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # DejaVu Bold
                f"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Liberation Bold
                f"/System/Library/Fonts/{font_name}.ttf",  # macOS
                f"C:/Windows/Fonts/{font_name}.ttf",  # Windows
            ]
            for path in common_paths:
                if os.path.exists(path):
                    try:
                        test_font = ImageFont.truetype(path, size=20)
                        return path
                    except (OSError, IOError):
                        continue
    
    # Fallback to bold system fonts (good for YouTube Shorts)
    fallback_fonts = [
        "DejaVu-Sans-Bold",
        "Liberation-Sans-Bold", 
        "Ubuntu-Bold",
        "Arial-Bold",
        "Arial"
    ]
    for font_name in fallback_fonts:
        try:
            test_font = ImageFont.truetype(font_name, size=20)
            return font_name
        except (OSError, IOError):
            continue
    
    return None  # Will use system default

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

    # Find available font - prioritize bold YouTube-friendly fonts
    preferred_fonts = [
        font,  # User's preferred font (Impact)
        "Impact",  # Perfect for YouTube Shorts - bold and thick
        "Arial-Black",  # Very bold, great for shorts
        "DejaVu-Sans-Bold",  # Common Linux bold font
        "Liberation-Sans-Bold",  # Common Linux bold font
        "Ubuntu-Bold"  # Ubuntu bold font
    ]
    actual_font = find_available_font(preferred_fonts)
    if actual_font != font:
        print(f"⚠️  Font '{font}' not found, using '{actual_font}' instead")
    elif actual_font is None:
        print("⚠️  No preferred fonts found, using system default")
        actual_font = None  # Let MoviePy use default
    else:
        print(f"✓ Using font: {actual_font}")

    # Get list of files to process
    files_to_process = [f for f in sorted(os.listdir(combined_folder)) if f.endswith(".mp4")]
    
    if not files_to_process:
        print("No video files found to process.")
        return
    
    print(f"Processing {len(files_to_process)} videos...")
    
    for file in tqdm(files_to_process, desc="   Burning subtitles", unit="video"):
        base = file.replace(".mp4", "")
        video_path = os.path.join(combined_folder, file)
        srt_path = os.path.join(subtitles_folder, f"{base}.srt")

        if not os.path.exists(srt_path):
            tqdm.write(f"⚠️  No matching subtitles for {file}, skipping.")
            continue

        random_name = uuid.uuid4().hex[:8]
        output_path = os.path.join(output_folder, f"{random_name}.mp4")

        tqdm.write(f"   Processing: {file} -> {random_name}.mp4")

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

            # create TextClips per word, randomly highlight with bright colors
            word_clips = []
            # Bright accent colors for random words
            accent_colors = ["#FF4444", "#44FF44", "#FFAA00", "#FF44FF", "#44AAFF", "#FFFF44"]

            MIN_WIDTH = int(video.w * 0.10)  # Minimum is 10% of video width, prevents zero width
            for word in words:
                if random.random() < highlight_prob:
                    color_choice = random.choice(accent_colors)
                else:
                    color_choice = "white"
                width_per_word = max(int(video.w // max(len(words), 1)), MIN_WIDTH)
                clip_kwargs = {
                    "text": word,
                    "font_size": fontsize,
                    "color": color_choice,
                    "stroke_color": stroke_color,
                    "stroke_width": stroke_width,
                    "method": "caption",
                    "size": (width_per_word, int(video.h * max_height_ratio)),
                }
                if actual_font:
                    clip_kwargs["font"] = actual_font
                word_clip = TextClip(**clip_kwargs)
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

                w = w.with_start(start).with_end(end).with_position(make_position)
                subtitle_clips.append(w)
                x_cursor += w.w

        final = CompositeVideoClip([video, *subtitle_clips])
        final.write_videofile(output_path,
                              codec="libx264",
                              audio_codec="aac",
                              fps=fps)
        video.close()
        final.close()
    
    print(f"✓ Completed burning subtitles to {len(files_to_process)} videos")
