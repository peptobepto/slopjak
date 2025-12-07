# slopjak
AI shitslop powered youtube short generator 

## Setup Instructions for Linux

### 1. System Dependencies

Install the following system packages using your package manager:

#### For Debian/Ubuntu:
```bash
sudo apt update
sudo apt install -y ffmpeg imagemagick python3-pip python3-venv
```

#### For Fedora/RHEL:
```bash
sudo dnf install -y ffmpeg ImageMagick python3-pip
```

#### For Arch Linux:
```bash
sudo pacman -S ffmpeg imagemagick python-pip
```

### 2. Install Ollama (for AI clip rating)

Ollama is required for the `ranker.py` module. Install it from [ollama.ai](https://ollama.ai) or:

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

Then pull the required model:
```bash
ollama pull llama3.1:8b
```

### 3. Python Environment Setup

Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 4. Verify Installation

Check that all required tools are available:
```bash
# Check ffmpeg
ffmpeg -version

# Check ImageMagick
magick -version  # or: convert -version

# Check ollama
ollama --version

# Check Python packages
python3 -c "import yt_dlp, faster_whisper, torch, moviepy, pysrt; print('All packages installed!')"
```

### 5. Configuration

The project auto-detects ImageMagick on Linux. If you have issues, you can manually set the path in `config.py` or `subtitles.py`.

### 6. Usage

Before running, ensure you have:
- Video files named `podcast.mp4` and `fart.mp4` in the project directory, OR
- Modify `main.py` to download videos using the `downloader.py` module

Then run:
```bash
# Activate the virtual environment first
source venv/bin/activate

# Then run the program
python3 main.py
```

Or run directly with the venv Python:
```bash
./venv/bin/python3 main.py
```

## Project Structure

- `downloader.py` - Downloads videos from YouTube
- `clipper.py` - Splits videos into clips using ffmpeg
- `transcriber.py` - Transcribes audio using faster-whisper
- `ranker.py` - Rates clips using Ollama LLM
- `cleaner.py` - Keeps only top-rated clips
- `combiner.py` - Combines podcast and gameplay clips in portrait format
- `subtitles.py` - Burns animated subtitles onto videos
- `main.py` - Main pipeline orchestrator

## Notes

- The project expects `podcast.mp4` and `fart.mp4` as input files
- Output folders: `podcast_output/`, `gameplay/`, `combined/`, `final_with_subs/`
- Make sure you have sufficient disk space for video processing
