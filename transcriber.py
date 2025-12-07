# File: transcriber.py
import os
from faster_whisper import WhisperModel


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


