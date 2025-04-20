import requests
import os
from dotenv import load_dotenv

load_dotenv()
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://192.168.0.124:7001")
FASTAPI_URL2 = os.getenv("FASTAPI_URL2", "http://192.168.0.20:7001")

class Penny:
    def __init__(self):
        pass

    def transcribe(self, audio_path=None):
        try:
            if audio_path is None:
                print("[Penny] No audio file provided for transcription.")
                return None

            with open(audio_path, "rb") as f:
                files = {"file": f}
                response = requests.post(f"{FASTAPI_URL2}/transcribe", files=files)

            if response.status_code == 200:
                return response.json().get("text", "")
            else:
                return None
        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    def respond(self, prompt):
        try:
            payload = {
                "instruction": "",
                "input": prompt
            }
            response = requests.post(f"{FASTAPI_URL}/respond", json=payload)
            if response.status_code == 200:
                return response.json().get("output", "")
            else:
                return None
        except Exception as e:
            print(f"Response error: {e}")
            return None