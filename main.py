# File: main.py
from downloader import download_video
from clipper import split_video_ffmpeg
from transcriber import transcribe_to_srt
from ranker import rate_clips
from cleaner import cleanup_and_rename_clips
from combiner import combine_portrait
from subtitles import burn_all_subtitles
from ascii_tools import splash_screen, play_ascii_gif_threaded, ascii_art
from config import IMAGEMAGICK_BINARY, PODCAST_FILENAME, FART_FILENAME
from faster_whisper import WhisperModel
import torch
import time
import os



def main():
    splash_screen(ascii_art)
time.sleep(1)



# Step 6: Burn meme-style animated subtitles
burn_all_subtitles(
combined_folder="combined",
subtitles_folder="subtitles",
output_folder="final_with_subs",
fontsize=60,
font="Modak",
color="#FFD24A",
stroke_color="black",
stroke_width=2,
fps=30,
max_height_ratio=0.25
)


# Final cleanup (optional)
from utils import delete_files_in_folders
delete_files_in_folders()


print("All steps completed! Final videos with animated subtitles are in 'final_with_subs/'")




if __name__ == "__main__":
    main()