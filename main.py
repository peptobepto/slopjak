# File: main.py
from downloader import download_video
from clipper import split_video_ffmpeg, extract_clip_by_timestamp
from transcriber import transcribe_video, extract_subtitle_segment
from ranker import pick_dynamic_segments
from combiner import combine_portrait
from subtitles import burn_all_subtitles
from ascii_tools import splash_screen, play_ascii_gif_threaded, ascii_art
from config import IMAGEMAGICK_BINARY, PODCAST_FILENAME, FART_FILENAME
from utils import delete_files_in_folders, cleanup_intermediate_files
import torch
import time
import os
import json
import sys

# Add cuDNN library path for CTranslate2 (used by faster-whisper)
# This helps CTranslate2 find the cuDNN libraries bundled with PyTorch
if torch.cuda.is_available():
    try:
        import site
        import ctypes
        # Find nvidia cudnn lib path
        for site_pkg in site.getsitepackages():
            cudnn_path = os.path.join(site_pkg, "nvidia", "cudnn", "lib")
            if os.path.exists(cudnn_path):
                # Set LD_LIBRARY_PATH for child processes
                current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
                if cudnn_path not in current_ld_path:
                    os.environ["LD_LIBRARY_PATH"] = f"{cudnn_path}:{current_ld_path}" if current_ld_path else cudnn_path
                
                # Load all cuDNN libraries in the correct order (main library first, then others)
                # This ensures all dependencies are available when CTranslate2 needs them
                cudnn_libs = [
                    "libcudnn.so.9",           # Main library (must be first)
                    "libcudnn_ops.so.9",      # Operations library
                    "libcudnn_cnn.so.9",      # CNN library (needed for convolution)
                    "libcudnn_adv.so.9",      # Advanced functions
                    "libcudnn_graph.so.9",    # Graph operations
                    "libcudnn_heuristic.so.9", # Heuristics
                    "libcudnn_engines_precompiled.so.9",  # Precompiled engines
                    "libcudnn_engines_runtime_compiled.so.9",  # Runtime compiled engines
                ]
                
                loaded_libs = []
                for lib_name in cudnn_libs:
                    lib_path = os.path.join(cudnn_path, lib_name)
                    if os.path.exists(lib_path):
                        try:
                            ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
                            loaded_libs.append(lib_name)
                        except Exception as e:
                            # Library might already be loaded or have dependencies
                            pass
                
                print(f"Configured cuDNN library path: {cudnn_path}")
                if loaded_libs:
                    print(f"Loaded {len(loaded_libs)} cuDNN libraries")
                break
    except Exception as e:
        print(f"Warning: Could not configure cuDNN library path: {e}")

from faster_whisper import WhisperModel


def main():
    splash_screen(ascii_art)
    time.sleep(1)
    
    # Check if we should clean up from previous run
    has_intermediate_files = (
        os.path.exists("full_podcast.srt") or
        os.path.exists("clip_ratings.json") or
        os.path.exists("subtitles") or
        os.path.exists("podcast_output") or
        os.path.exists("gameplay") or
        os.path.exists("combined") or
        os.path.exists("final_with_subs")
    )
    
    if has_intermediate_files:
        print("\n=== Previous run cleanup detected ===")
        response = input("Found files from a previous run. Clean them up now? (y/n): ").strip().lower()
        if response == 'y':
            delete_originals = input("Also delete original video files (podcast.mp4, fart.mp4)? (y/n): ").strip().lower() == 'y'
            cleanup_intermediate_files(keep_originals=not delete_originals)
        else:
            print("Keeping previous files. They may be overwritten.")
    
    # Use try/finally to ensure cleanup happens even on failure
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        raise
    except Exception as e:
        print(f"\n\n✗ Error during pipeline execution: {e}")
        print("Cleaning up intermediate files...")
        cleanup_intermediate_files(keep_originals=True)
        raise
    finally:
        # Always cleanup intermediate files on completion (success or failure)
        # Keep final output folder and original videos
        print("\n=== Final cleanup ===")
        cleanup_intermediate_files(keep_originals=True, keep_final_output=True)


def run_pipeline():
    """Main pipeline execution (separated for error handling)."""

    # Step 1: Download videos from user input
    print("\n=== Step 1: Video Download ===")
    
    # Check if files already exist
    podcast_exists = os.path.exists(PODCAST_FILENAME)
    fart_exists = os.path.exists(FART_FILENAME)
    
    if podcast_exists and fart_exists:
        print(f"Found existing files: {PODCAST_FILENAME} and {FART_FILENAME}")
        response = input("Do you want to download new videos? (y/n): ").strip().lower()
        if response != 'y':
            print("Using existing video files.")
        else:
            podcast_exists = False
            fart_exists = False
    
    # Download podcast video if needed
    if not podcast_exists:
        podcast_url = input(f"Enter YouTube URL for podcast video (will save as {PODCAST_FILENAME}): ").strip()
        if podcast_url:
            try:
                download_video(podcast_url, PODCAST_FILENAME)
            except Exception as e:
                print(f"Failed to download podcast video: {e}")
                return
        else:
            print("No URL provided. Skipping podcast download.")
            if not os.path.exists(PODCAST_FILENAME):
                print(f"Error: {PODCAST_FILENAME} not found. Cannot continue.")
                return
    
    # Download gameplay video if needed
    if not fart_exists:
        fart_url = input(f"Enter YouTube URL for gameplay video (will save as {FART_FILENAME}): ").strip()
        if fart_url:
            try:
                download_video(fart_url, FART_FILENAME)
            except Exception as e:
                print(f"Failed to download gameplay video: {e}")
                print("Continuing without gameplay video (combining step will be skipped)...")
        else:
            print("No URL provided. Skipping gameplay download.")

    # Step 2: Split gameplay video into clips (still needed for combining)
    print("\n=== Step 2: Splitting gameplay video into clips ===")
    if os.path.exists(FART_FILENAME):
        split_video_ffmpeg(FART_FILENAME, clip_length=60)
    else:
        print(f"Warning: {FART_FILENAME} not found. Skipping gameplay splitting.")

    # Step 3: Initialize Whisper model for transcription
    print("\n=== Step 3: Initializing Whisper model ===")
    # Try CUDA first, but fall back to CPU if there are issues
    use_cuda = False
    if torch.cuda.is_available():
        try:
            # Test if CUDA actually works with PyTorch
            test_tensor = torch.zeros(1).cuda()
            del test_tensor
            torch.cuda.empty_cache()
            
            # Test if CTranslate2 (used by faster-whisper) can access CUDA
            import ctranslate2
            if ctranslate2.get_cuda_device_count() > 0:
                use_cuda = True
                print(f"CUDA available (GPU: {torch.cuda.get_device_name(0)}), using GPU")
            else:
                print("CUDA available in PyTorch but not in CTranslate2, using CPU")
        except Exception as e:
            print(f"CUDA detected but not working properly: {e}")
            print("Falling back to CPU")
            use_cuda = False
    else:
        print("CUDA not available, using CPU")
    
    if not use_cuda:
        print("Using CPU for transcription (this will be slower but more stable)")
    
    device = "cuda" if use_cuda else "cpu"
    # Use float16 for GPU (faster), int8 for CPU (more memory efficient)
    compute_type = "float16" if use_cuda else "int8"
    
    # Try to load model with error handling
    model = None
    try:
        print(f"Loading Whisper 'base' model on {device.upper()}...")
        model = WhisperModel("base", device=device, compute_type=compute_type)
        print(f"✓ Whisper model loaded successfully on {device.upper()}!")
    except Exception as e:
        print(f"✗ Error loading Whisper model with {device}: {e}")
        if use_cuda:
            print("Retrying with CPU...")
            try:
                model = WhisperModel("base", device="cpu", compute_type="int8")
                print("✓ Whisper model loaded on CPU!")
            except Exception as e2:
                print(f"✗ Failed to load on CPU as well: {e2}")
                raise
        else:
            raise
    
    if model is None:
        raise RuntimeError("Failed to initialize Whisper model")

    # Step 4: Transcribe full podcast video (not split yet!)
    print("\n=== Step 4: Transcribing full podcast video ===")
    full_podcast_srt = "full_podcast.srt"
    if os.path.exists(PODCAST_FILENAME):
        transcribe_video(PODCAST_FILENAME, full_podcast_srt, model=model)
    else:
        print(f"Error: {PODCAST_FILENAME} not found. Cannot continue.")
        return

    # Step 5: Use AI to pick dynamic segments from full transcript
    print("\n=== Step 5: AI picking dynamic segments ===")
    segments = pick_dynamic_segments(full_podcast_srt, num_segments=5, target_duration=60)
    
    if not segments:
        print("Error: No segments were picked. Cannot continue.")
        return
    
    # Step 6: Extract video clips and subtitle segments for picked segments
    print("\n=== Step 6: Extracting dynamic clips and subtitles ===")
    os.makedirs("podcast_output", exist_ok=True)
    os.makedirs("subtitles", exist_ok=True)
    
    # Save segment info for later use
    segment_data = []
    
    from tqdm import tqdm
    print(f"Extracting {len(segments)} clips...")
    
    for i, seg in enumerate(tqdm(segments, desc="   Extracting clips", unit="clip"), start=1):
        start_sec = seg["start_seconds"]
        duration_sec = seg["duration_seconds"]
        
        # Extract video clip
        clip_filename = f"{i}.mp4"
        clip_path = os.path.join("podcast_output", clip_filename)
        extract_clip_by_timestamp(PODCAST_FILENAME, start_sec, duration_sec, clip_path)
        
        # Extract corresponding subtitle segment
        srt_filename = f"{i}.srt"
        srt_path = os.path.join("subtitles", srt_filename)
        extract_subtitle_segment(full_podcast_srt, start_sec, duration_sec, srt_path)
        
        # Store segment info
        segment_data.append({
            "clip": srt_filename,
            "rating": seg["rating"],
            "reason": seg["reason"],
            "start_seconds": start_sec,
            "duration_seconds": duration_sec
        })
    
    # Save ratings (for compatibility with existing code)
    with open("clip_ratings.json", "w", encoding="utf-8") as f:
        json.dump(segment_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(segment_data)} dynamic clips with ratings")

    # Step 7: Combine podcast and gameplay clips in portrait format
    print("\n=== Step 7: Combining clips in portrait format ===")
    combine_portrait("podcast_output", "gameplay", "combined")

    # Step 8: Burn meme-style animated subtitles
    print("\n=== Step 8: Burning animated subtitles ===")
    if os.path.exists("combined") and os.path.exists("subtitles"):
        import glob
        combined_files = glob.glob("combined/*.mp4")
        if combined_files:
            print(f"Found {len(combined_files)} videos to process...")
        burn_all_subtitles(
            combined_folder="combined",
            subtitles_folder="subtitles",
            output_folder="final_with_subs",
            fontsize=80,  # Large size for YouTube Shorts
            font="Impact",  # Bold, thick font
            color="white",  # Base white color - will be randomly changed per word
            stroke_color="black",
            stroke_width=3,  # Thick black outline for readability
            fps=30,
            max_height_ratio=0.25,
            highlight_prob=0.15  # 15% chance for each word to be colored
        )
    else:
        print("Warning: combined or subtitles folder not found. Skipping subtitle burning.")

    # Step 9: Pipeline complete
    print("\n" + "="*50)
    print("✓ All steps completed! Final videos with animated subtitles are in 'final_with_subs/'")
    print("="*50)
    # Note: Cleanup happens in the finally block of main()


if __name__ == "__main__":
    main()