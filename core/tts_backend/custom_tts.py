from pathlib import Path
import requests
from core.utils.config_utils import load_key

def custom_tts(text, save_path):
    """
    Custom TTS (Text-to-Speech) interface
    
    Args:
        text (str): Text to be converted to speech
        save_path (str): Path to save the audio file
        
    Returns:
        None
    
    Example:
        custom_tts("Hello world", "output.wav")
    """
    # Ensure save directory exists
    speech_file_path = Path(save_path)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        url = load_key("custom_tts.base_url")
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        data = {
            "input": text,
            "response_format": "wav",
            "emotion": "普通",
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for bad responses
        with open(speech_file_path, 'wb') as f:
            f.write(response.content)
        print(f"Audio saved to {speech_file_path}")
    except Exception as e:
        print(f"Error occurred during TTS conversion: {str(e)}")
        raise e

if __name__ == "__main__":
    # Test example
    custom_tts("This is a test.", "custom_tts_test.wav")
