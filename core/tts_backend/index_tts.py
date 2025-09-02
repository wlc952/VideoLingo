from pathlib import Path
import requests
from core.utils.config_utils import load_key
from core.utils.models import _AUDIO_REFERS_DIR
from core.utils import rprint

def index_tts(ref_audio_path, text, save_path):
    # Ensure save directory exists
    speech_file_path = Path(save_path)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        url = load_key("index_tts.base_url")
        headers = {
            'accept': 'application/json'
        }
        # Upload reference audio as multipart/form-data with text field
        ref_path = Path(ref_audio_path)
        if not ref_path.exists():
            raise FileNotFoundError(f"Reference audio not found: {ref_path}")
        with open(ref_path, 'rb') as f:
            files = {
                'ref_audio_file': (ref_path.name, f, 'audio/vnd.wave')
            }
            data = {
                'text': text
            }
            response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()  # Raise an error for bad responses
        with open(speech_file_path, 'wb') as f:
            f.write(response.content)
        print(f"Audio saved to {speech_file_path}")
    except Exception as e:
        print(f"Error occurred during TTS conversion: {str(e)}")
        raise e


def index_tts_for_videolingo(text, save_as, number, task_df):
    """Adapter to use VideoLingo's extracted reference audio to call index_tts.

    Contract:
    - Inputs: text(str), save_as(str), number(int), task_df(DataFrame)
    - Behavior: prefer per-line ref audio `${_AUDIO_REFERS_DIR}/{number}.wav`,
      else fallback to `1.wav`. If not present, try to extract via core._9_refer_audio.
    - Output: writes wav to save_as; raises on hard errors.
    """
    current_dir = Path.cwd()

    # Prefer the same-number reference; fallback to 1.wav
    ref_audio_path = current_dir / f"{_AUDIO_REFERS_DIR}/{number}.wav"
    if not ref_audio_path.exists():
        fallback = current_dir / f"{_AUDIO_REFERS_DIR}/1.wav"
        if not fallback.exists():
            # Try to extract reference audios from the vocal track
            try:
                from core._9_refer_audio import extract_refer_audio_main
                rprint("[yellow]Reference audio not found, extracting from source vocal track...[/yellow]")
                extract_refer_audio_main()
            except Exception as e:
                rprint(f"[bold red]Failed to extract reference audio: {str(e)}[/bold red]")
                raise
        ref_audio_path = fallback if fallback.exists() else ref_audio_path

    # Call the raw index_tts
    return index_tts(str(ref_audio_path), text, save_as)

if __name__ == "__main__":
    # Test example
    index_tts("ref_audio.wav", "This is a test.", "index_tts.wav")