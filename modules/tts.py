import subprocess, requests
import sounddevice as sd
from pydub import AudioSegment
from modules.audio_modifier import modify_audio
import tempfile
import os, regex, threading
import numpy as np

PIPER_PATH = "F:\\Penny2\\Piper\\piper\\piper.exe"
VOICE_MODEL = "F:\\Penny2\\Piper\\piper\\voices\\glados.onnx"
VAC_OUTPUT_NAME = "CABLE Input (VB-Audio Virtual Cable)"

def remove_emojis(text):
    emoji_pattern = regex.compile(
        r'[\p{Emoji_Presentation}\p{Emoji}\p{Extended_Pictographic}]',
        flags=regex.UNICODE
    )
    return emoji_pattern.sub(r'', text)

class TTS:
    def __init__(self):
        self.output_device = self.find_output_device(VAC_OUTPUT_NAME)
        self.volume_db = 4
        self.is_speaking = False
        self.collab_mode = False

    def find_output_device(self, name):
        devices = sd.query_devices()
        for idx, device in enumerate(devices):
            if name.lower() in device['name'].lower() and device['max_output_channels'] > 0:
                print(f"[TTS] Found output device: {device['name']} (id {idx})")
                return idx
        raise RuntimeError(f"Output device '{name}' not found!")

    def speak(self, text):
        safe_text = remove_emojis(text)
        wav_path = self.generate_wav(safe_text)
        modified_audio = modify_audio(wav_path, speed=1.8, semitones=-10)
        modified_audio = modified_audio - self.volume_db
        samples = np.array(modified_audio.get_array_of_samples())
        samples = samples.astype(np.float32) / (2 ** 15)

        # Always export Discord version first if collab mode
        if self.collab_mode:
            try:
                discord_path = wav_path.replace(".wav", "_discord.wav")
                modified_audio.export(discord_path, format="wav")
                with open(discord_path, "rb") as f:
                    r = requests.post("http://192.168.0.20:7001/discord", files={"file": f})
                    print(f"[TTS] Sent to Discord: {r.status_code}")
                os.remove(discord_path)
            except Exception as e:
                print(f"[TTS] Error sending to Discord: {e}")

        self.is_speaking = True

        try:
            print(f"[TTS] Playing WAV: {wav_path} | Length: {len(samples)} samples")
            sd.play(samples, samplerate=modified_audio.frame_rate, device=self.output_device)
        except Exception as e:
            print(f"[TTS] Error during playback: {e}")

        # Background wait
        def wait_and_reset():
            try:
                sd.wait()
            except Exception as e:
                print(f"[TTS] Error waiting for playback to finish: {e}")
            self.is_speaking = False

        threading.Thread(target=wait_and_reset, daemon=True).start()

        if os.path.exists(wav_path):
            os.remove(wav_path)

    def generate_wav(self, text):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        wav_path = tmp.name
        tmp.close()

        try:
            subprocess.run(
                [PIPER_PATH, "--model", VOICE_MODEL, "--output_file", wav_path],
                input=text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"[TTS] Piper error: {e}")
        return wav_path
