import tkinter as tk
from tkinter import scrolledtext
import threading
import os, regex, time
from penny import Penny
from modules.tts import TTS
from modules.recorder import record_audio_chunk
from modules.twitch_bot import launch_twitch_bot_thread
from modules.manual_recording import ManualRecorder
from modules.speech_queue import SpeechQueue  # Shared global speech_queue

speech_queue = SpeechQueue()

class PennyDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Penny Dashboard")
        self.root.configure(bg="#1e1e2f")  # Dark background
        self.muted = False
        self.penny = Penny()
        self.tts = TTS()
        self.listening = False

        self.setup_ui()

        # Start Twitch bot with shared queue
        launch_twitch_bot_thread()

    def setup_ui(self):
        self.talk_light = tk.Canvas(self.root, width=30, height=30, bg="gray", highlightthickness=0)
        self.talk_light.pack(pady=10)

        self.status_label = tk.Label(self.root, text="Status: Idle", font=("Arial", 12), bg="#1e1e2f", fg="#c586ff")
        self.status_label.pack(pady=5)

        button_style = {"bg": "#2e2e3e", "fg": "white", "activebackground": "#5e5e9e", "activeforeground": "white", "font": ("Arial", 10)}

        self.start_button = tk.Button(self.root, text="Start Listening", command=self.start_listening, **button_style)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self.root, text="Stop Listening", command=self.stop_listening, **button_style)
        self.stop_button.pack(pady=5)

        self.restart_button = tk.Button(self.root, text="Restart Penny", command=self.restart_penny, **button_style)
        self.restart_button.pack(pady=5)

        self.mute_button = tk.Button(self.root, text="Mute Penny", command=self.toggle_mute, **button_style)
        self.mute_button.pack(pady=5)

        self.start_manual_button = tk.Button(self.root, text="Start Recording", command=self.start_manual_recording, **button_style)
        self.start_manual_button.pack(pady=5)

        self.stop_manual_button = tk.Button(self.root, text="Stop Recording", command=self.stop_manual_recording, **button_style)
        self.stop_manual_button.pack(pady=5)

        self.push_to_talk_button = tk.Button(self.root, text="Enable Push-to-Talk", command=self.launch_push_to_talk, **button_style)
        self.push_to_talk_button.pack(pady=5)

        self.volume_slider = tk.Scale(self.root, from_=0, to=20, orient='horizontal', label="Volume (dB Reduction)",
                                      command=self.update_volume, bg="#1e1e2f", fg="white", troughcolor="#5e5e9e", highlightthickness=0)
        self.volume_slider.set(4)
        self.volume_slider.pack(pady=10)

        self.log_area = scrolledtext.ScrolledText(self.root, width=65, height=12, bg="#2e2e3e", fg="white", insertbackground="white")
        self.log_area.pack(pady=10)
        self.log_area.configure(state='disabled')

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.manual_recorder = ManualRecorder(
            penny=self.penny,
            tts=self.tts,
            speech_queue=speech_queue,
            log_func=self.log,
            remove_emojis_func=self.remove_emojis
        )

    def start_manual_recording(self):
        self.manual_recorder.start_recording()

    def stop_manual_recording(self):
        self.manual_recorder.stop_recording()

    def launch_push_to_talk(self):
        threading.Thread(target=self.manual_recorder.listen_for_push_to_talk, daemon=True).start()
        self.log("[Main] Push-to-Talk mode enabled.")

    def toggle_mute(self):
        self.muted = not self.muted
        status = "Muted" if self.muted else "Unmuted"
        self.log(f"[Mute] Penny is now {status}.")
        self.mute_button.config(text="Unmute Penny" if self.muted else "Mute Penny")

    def update_volume(self, value):
        try:
            self.tts.volume_db = float(value)
            self.log(f"[Volume] Penny volume set to {value} dB reduction.")
        except Exception as e:
            self.log(f"[Volume] Error updating volume: {e}")

    @staticmethod
    def remove_emojis(text):
        emoji_pattern = regex.compile(r'[\p{Emoji_Presentation}\p{Emoji}\p{Extended_Pictographic}]', flags=regex.UNICODE)
        return emoji_pattern.sub(r'', text)

    def on_close(self):
        from modules.twitch_bot import stop_twitch_bot
        stop_twitch_bot()
        self.root.destroy()

    def log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

    def set_light_listening(self):
        self.talk_light.config(bg="green")
        self.status_label.config(text="Status: Listening...")

    def set_light_speaking(self):
        self.talk_light.config(bg="red")
        self.status_label.config(text="Status: Speaking...")

    def set_light_idle(self):
        self.talk_light.config(bg="gray")
        self.status_label.config(text="Status: Idle")

    def start_listening(self):
        if not self.listening:
            self.listening = True
            self.set_light_listening()
            threading.Thread(target=self.listen_loop, daemon=True).start()
            self.log("[Main] Started listening...")

    def stop_listening(self):
        self.listening = False
        self.set_light_idle()
        self.log("[Main] Stopped listening.")

    def restart_penny(self):
        self.stop_listening()
        self.start_listening()
        self.log("[Main] Restarted Penny.")

    def listen_loop(self):
        while self.listening:
            self.log("[Main] Recording 10s audio chunk...")
            audio_path = record_audio_chunk(duration=10)
            transcription = self.penny.transcribe(audio_path)

            if transcription:
                cleaned = transcription.strip()
                if cleaned == "" or cleaned.replace(".", "").strip() == "":
                    self.log("[Main] Ignored empty or invalid transcription.")
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    continue

                self.log(f"[Main] Transcribed: {cleaned}")
                self.set_light_idle()

                response = self.penny.respond(cleaned)
                if response:
                    self.log(f"Penny: {response}")
                    safe_response = self.remove_emojis(response)
                    self.set_light_speaking()

                    if not self.muted:
                        speech_queue.add_to_queue(safe_response)
                    else:
                        self.log("[Mute] Penny is muted and did not speak.")

                    self.set_light_listening()

            if os.path.exists(audio_path):
                os.remove(audio_path)
