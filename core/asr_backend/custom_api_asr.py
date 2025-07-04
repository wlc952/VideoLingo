import os
import json
import time
import requests
import tempfile
import librosa
import soundfile as sf
from rich import print as rprint
from core.utils import *


def transcribe_audio_custom_api(raw_audio_path, vocal_audio_path, start=None, end=None):
    rprint(
        f"[cyan]🎤 Processing audio transcription, file path: {vocal_audio_path}[/cyan]"
    )
    LOG_FILE = f"output/log/elevenlabs_transcribe_{start}_{end}.json"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # Load audio and process start/end parameters
    y, sr = librosa.load(vocal_audio_path, sr=16000)
    audio_duration = len(y) / sr

    if start is None or end is None:
        start = 0
        end = audio_duration

    # Slice audio based on start/end
    start_sample = int(start * sr)
    end_sample = int(end * sr)
    y_slice = y[start_sample:end_sample]

    # Create temporary file for the sliced audio
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_filepath = temp_file.name
        sf.write(temp_filepath, y_slice, sr, format="MP3")

    try:
        base_url = load_key("whisper.custom_api_url")
        data = {
            "language": load_key("whisper.language"),
            "word_timestamps": True,
        }

        with open(temp_filepath, "rb") as audio_file:
            files = {
                "file": (os.path.basename(temp_filepath), audio_file, "audio/mpeg")
            }
            start_time = time.time()
            response = requests.post(base_url, data=data, files=files)

        rprint(
            f"[yellow]API request sent, status code: {response.status_code}[/yellow]"
        )
        result = response.json()

        # save detected language
        detected_language = result.get("language", "en")
        update_key("whisper.detected_language", detected_language)

        # Adjust timestamps for all segments and words by adding the start time
        if start is not None and "segments" in result:
            for segment in result["segments"]:
                if "start" in segment:
                    segment["start"] += start
                if "end" in segment:
                    segment["end"] += start
                # Adjust word timestamps if they exist
                if "words" in segment:
                    for word in segment["words"]:
                        if "start" in word:
                            word["start"] += start
                        if "end" in word:
                            word["end"] += start

        rprint(
            f"[green]✓ Transcription completed in {time.time() - start_time:.2f} seconds[/green]"
        )

        # The API already returns Whisper format, no need to convert
        parsed_result = result

        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(parsed_result, f, indent=4, ensure_ascii=False)
        return parsed_result
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


if __name__ == "__main__":
    file_path = input("Enter local audio file path (mp3 format): ")
    language = input("Enter language code for transcription (en or zh or other...): ")
    result = transcribe_audio_custom_api(file_path, language_code=language)
    print(result)

    # Save result to file
    with open("output/transcript.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
