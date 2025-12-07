# File: transcriber.py
import os
from faster_whisper import WhisperModel
import pysrt
from tqdm import tqdm
import subprocess
import json


# Re-usable SRT formatter for faster-whisper segments
def format_srt(segments):
    def srt_time(seconds):
        ms = int((seconds % 1) * 1000)
        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"

    srt_lines = []
    for i, seg in enumerate(segments, start=1):
        start = srt_time(seg.start)
        end = srt_time(seg.end)
        text = seg.text.strip()
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")

    return "\n".join(srt_lines)


def transcribe_to_srt(input_folder, output_folder="subtitles", model: WhisperModel = None):
    if model is None:
        raise ValueError("Model must be provided")

    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(input_folder):
        if not file.endswith(".mp4"):
            continue

        clip_path = os.path.join(input_folder, file)
        srt_path = os.path.join(output_folder, file.replace(".mp4", ".srt"))

        print(f"Transcribing {file}...")
        try:
            segments, info = model.transcribe(
                clip_path, language="en", vad_filter=True, word_timestamps=False
            )
            segments = list(segments)
            srt_text = format_srt(segments)

            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_text)

            print(f"Saved subtitles: {srt_path}")
        except Exception as e:
            print(f"Error transcribing {file}: {e}")

    print("Finished transcribing all clips.")


def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "json", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return None


def transcribe_video(video_path, output_srt_path, model: WhisperModel = None):
    """Transcribe a single video file to an SRT file with progress bar."""
    if model is None:
        raise ValueError("Model must be provided")
    
    os.makedirs(os.path.dirname(output_srt_path) if os.path.dirname(output_srt_path) else ".", exist_ok=True)
    
    video_name = os.path.basename(video_path)
    print(f"\n📹 Transcribing: {video_name}")
    
    # Get video duration for progress estimation
    duration = get_video_duration(video_path)
    if duration:
        print(f"   Video duration: {int(duration // 60)}m {int(duration % 60)}s")
    
    try:
        # Create progress bar
        pbar = tqdm(
            desc="   Transcription progress",
            unit="segments",
            dynamic_ncols=True,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} segments [{elapsed}<{remaining}]"
        )
        
        segments_list = []
        last_time = 0.0
        
        # Transcribe with progress tracking
        segments, info = model.transcribe(
            video_path, language="en", vad_filter=True, word_timestamps=False
        )
        
        # Process segments and update progress
        for segment in segments:
            segments_list.append(segment)
            current_time = segment.end
            
            # Update progress bar
            if duration:
                # Estimate progress based on time
                progress_pct = min(100, (current_time / duration) * 100)
                pbar.set_postfix({"time": f"{int(current_time // 60)}m {int(current_time % 60)}s", "progress": f"{progress_pct:.1f}%"})
            else:
                pbar.set_postfix({"segments": len(segments_list)})
            
            pbar.update(1)
            last_time = current_time
        
        pbar.close()
        
        # Format and save
        print(f"   Processing {len(segments_list)} segments...")
        srt_text = format_srt(segments_list)
        
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write(srt_text)
        
        print(f"✓ Saved subtitles: {output_srt_path}")
        print(f"   Total transcription time: {int(last_time // 60)}m {int(last_time % 60)}s")
        return output_srt_path
    except Exception as e:
        print(f"✗ Error transcribing {video_path}: {e}")
        raise


def extract_subtitle_segment(full_srt_path, start_seconds, duration_seconds, output_srt_path):
    """Extract a subtitle segment from a full SRT file for a specific time range.
    
    Args:
        full_srt_path: Path to the full SRT file
        start_seconds: Start time in seconds
        duration_seconds: Duration in seconds
        output_srt_path: Path for the output SRT segment
    """
    end_seconds = start_seconds + duration_seconds
    
    # Load full subtitles
    subs = pysrt.open(full_srt_path)
    
    # Filter subtitles that fall within the time range
    segment_subs = []
    for sub in subs:
        sub_start = sub.start.ordinal / 1000.0
        sub_end = sub.end.ordinal / 1000.0
        
        # Include subtitle if it overlaps with our segment
        if sub_start < end_seconds and sub_end > start_seconds:
            # Adjust timestamps relative to segment start
            adjusted_start = max(0, sub_start - start_seconds)
            adjusted_end = min(duration_seconds, sub_end - start_seconds)
            
            # Create new subtitle entry
            new_sub = pysrt.SubRipItem(
                index=len(segment_subs) + 1,
                start=pysrt.SubRipTime(seconds=int(adjusted_start), milliseconds=int((adjusted_start % 1) * 1000)),
                end=pysrt.SubRipTime(seconds=int(adjusted_end), milliseconds=int((adjusted_end % 1) * 1000)),
                text=sub.text
            )
            segment_subs.append(new_sub)
    
    # Save segment subtitles
    os.makedirs(os.path.dirname(output_srt_path) if os.path.dirname(output_srt_path) else ".", exist_ok=True)
    segment_file = pysrt.SubRipFile(segment_subs)
    segment_file.save(output_srt_path, encoding='utf-8')
    print(f"Extracted subtitle segment: {output_srt_path} ({len(segment_subs)} subtitle entries)")


