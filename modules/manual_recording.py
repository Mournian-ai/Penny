import threading
import time
import sounddevice as sd
import soundfile as sf
import tempfile
import os
import keyboard
import numpy as np
import wave

class ManualRecorder:
    def __init__(self, penny, tts, speech_queue, log_func, remove_emojis_func):
        self.penny = penny
        self.tts = tts
        self.speech_queue = speech_queue
        self.log = log_func
        self.remove_emojis = remove_emojis_func
        self.listening = False
        self.recorded_frames = []
        self.samplerate = 16000
        self.recording_thread = None
        self.push_to_talk_key = 'caps lock'  # Default PTT key

    def start_recording(self):
        if not self.listening:
            self.listening = True
            self.recorded_frames = []
            self.recording_thread = threading.Thread(target=self.record_audio_continuous, daemon=True)
            self.recording_thread.start()
            self.log("[Manual] Started manual recording.")

    def stop_recording(self):
        if self.listening:
            self.listening = False
            self.log("[Manual] Stopping manual recording...")

    def record_audio_continuous(self):
        def callback(indata, frames, time_info, status):
            if self.listening:
                self.recorded_frames.append(indata.copy())

        with sd.InputStream(samplerate=self.samplerate, channels=1, dtype='int16', callback=callback):
            while self.listening:
                sd.sleep(50)

        if self.recorded_frames:
            audio_data = np.concatenate(self.recorded_frames, axis=0)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp.close()

            with sf.SoundFile(tmp.name, mode='w', samplerate=self.samplerate, channels=1, subtype="PCM_16") as file:
                file.write(audio_data)

            self.log(f"[Manual] Saved recording to {tmp.name}")

            try:
                # Very short check (file length)
                if self.get_audio_duration(tmp.name) < 1.0:
                    self.log("[Manual] Recording too short, ignoring.")
                    os.remove(tmp.name)
                    return

                transcription = self.penny.transcribe(tmp.name)
                if transcription:
                    cleaned = transcription.strip()

                    # Empty or dots
                    if cleaned == "" or cleaned.replace(".", "").strip() == "":
                        self.log("[Manual] Ignored empty transcription.")
                        os.remove(tmp.name)
                        return

                    words = cleaned.split()
                    unique_words = set(words)

                    # Too short
                    if len(words) <= 2:
                        self.log("[Manual] Ignored too short transcription.")
                        os.remove(tmp.name)
                        return

                    # Garbage repeated
                    if len(unique_words) <= 2 and len(words) > 10:
                        self.log("[Manual] Ignored garbage repeated transcription.")
                        os.remove(tmp.name)
                        return

                    self.log(f"Transcribed: {cleaned}")

                    response = self.penny.respond(cleaned)
                    if response:
                        self.log(f"Penny: {response}")
                        safe_response = self.remove_emojis(response)
                        self.speech_queue.add_to_queue(safe_response)

            finally:
                time.sleep(0.2)
                if os.path.exists(tmp.name):
                    os.remove(tmp.name)

    def get_audio_duration(self, filepath):
        try:
            with wave.open(filepath, 'r') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return frames / float(rate)
        except Exception as e:
            self.log(f"[Manual] Error getting duration: {e}")
            return 0

    def listen_for_push_to_talk(self):
        self.log("[Manual] Push-to-Talk listener started...")
        while True:
            keyboard.wait(self.push_to_talk_key)
            self.start_recording()
            while keyboard.is_pressed(self.push_to_talk_key):
                time.sleep(0.05)
            self.stop_recording()
