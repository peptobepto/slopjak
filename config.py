# File: config.py
"""Configuration constants for the pipeline."""
import shutil

# Auto-detect ImageMagick binary for Linux
IMAGEMAGICK_BINARY = shutil.which("magick") or shutil.which("convert") or "convert"
PODCAST_FILENAME = "podcast.mp4"
FART_FILENAME = "fart.mp4"
