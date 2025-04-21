import tkinter as tk
from tkinter import scrolledtext
import threading
import os, regex, time, requests
from penny import Penny
from modules.tts import TTS
from modules.recorder import record_audio_chunk
from modules.manual_recording import ManualRecorder
from modules.speech_queue import SpeechQueue
from modules.twitch_bot import launch_twitch_bot_thread
import modules.mic_stream_client
class PennyDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Penny Dashboard")
        self.root.configure(bg="black")
        self.root.geometry("800x600")
        self.muted = False
        self.penny = Penny()
        self.tts = TTS()
        self.speech_queue = SpeechQueue(self.tts, self)
        self.listening = False

        self.setup_ui()

        self.manual_recorder = ManualRecorder(
            penny=self.penny,
            tts=self.tts,
            speech_queue=self.speech_queue,
            log_func=self.log,
            remove_emojis_func=self.remove_emojis
        )

    def setup_ui(self):
        button_frame = tk.Frame(self.root, bg="black")
        button_frame.pack(pady=10)

        self.main_server_status = tk.Label(root, text="Penny Main", bg="gray", fg="white", font=("Arial", 10), width=12)
        self.main_server_status.place(x=675, y=70)

        self.secondary_server_status = tk.Label(root, text="Penny 2", bg="gray", fg="white", font=("Arial", 10), width=12)
        self.secondary_server_status.place(x=675, y=100)
        self.update_server_status()

        self.talk_light = tk.Label(root, text="", bg="gray", width=2, height=1)
        self.talk_light.place(x=700, y=10)

        self.start_button = tk.Button(button_frame, text="Start Listening", command=self.start_listening, font=("Consolas", 12), bg="#800080", fg="white")
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(button_frame, text="Stop Listening", command=self.stop_listening, font=("Consolas", 12), bg="#800080", fg="white")
        self.stop_button.grid(row=0, column=1, padx=5)

        self.restart_button = tk.Button(button_frame, text="Restart Penny", command=self.restart_penny, font=("Consolas", 12), bg="#800080", fg="white")
        self.restart_button.grid(row=0, column=2, padx=5)

        self.mute_button = tk.Button(button_frame, text="Mute Penny", command=self.toggle_mute, font=("Consolas", 12), bg="#800080", fg="white")
        self.mute_button.grid(row=0, column=3, padx=5)

        ptt_frame = tk.Frame(self.root, bg="black")
        ptt_frame.pack(pady=5)

        self.start_manual_button = tk.Button(ptt_frame, text="Start PTT", command=self.manual_recorder_start, font=("Consolas", 12), bg="#800080", fg="white")
        self.start_manual_button.grid(row=0, column=0, padx=5)

        self.stop_manual_button = tk.Button(ptt_frame, text="Stop PTT", command=self.manual_recorder_stop, font=("Consolas", 12), bg="#800080", fg="white")
        self.stop_manual_button.grid(row=0, column=1, padx=5)

        self.push_to_talk_button = tk.Button(ptt_frame, text="Enable Push-to-Talk", command=self.launch_push_to_talk, font=("Consolas", 12), bg="#800080", fg="white")
        self.push_to_talk_button.grid(row=0, column=2, padx=5)

        self.status_label = tk.Label(self.root, text="Status: Idle", font=("Consolas", 14), bg="black", fg="white")
        self.status_label.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(self.root, width=80, height=25, font=("Consolas", 12), bg="black", fg="white", insertbackground="white")
        self.log_area.pack(pady=10)
        self.log_area.configure(state='disabled')

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        launch_twitch_bot_thread(self.speech_queue)

        
    def manual_recorder_start(self):
        self.manual_recorder.start_recording()

    def manual_recorder_stop(self):
        self.manual_recorder.stop_recording()

    def set_light_listening(self):
        self.talk_light.config(bg="green")
        self.status_label.config(text="Status: Listening...")

    def set_light_speaking(self):
        self.talk_light.config(bg="red")
        self.status_label.config(text="Status: Speaking...")

    def set_light_idle(self):
        self.talk_light.config(bg="gray")
        self.status_label.config(text="Status: Idle")

    def set_light_thinking(self):
        self.talk_light.config(bg="purple")
        self.status_label.config(text="Status: Thinking...")

    def launch_push_to_talk(self):
        threading.Thread(target=self.manual_recorder.listen_for_push_to_talk, daemon=True).start()
        self.log("[Main] Push-to-Talk mode enabled.")

    def toggle_mute(self):
        self.muted = not self.muted
        status = "Muted" if self.muted else "Unmuted"
        self.log(f"[Mute] Penny is now {status}.")
        self.mute_button.config(text="Unmute Penny" if self.muted else "Mute Penny")

    def remove_emojis(self, text):
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

    def start_listening(self):
        if not self.listening:
            self.listening = True
            self.status_label.config(text="Status: Listening...")
            modules.mic_stream_client.start_streaming()
            self.set_light_listening()
            self.log("Started listening...")

    def stop_listening(self):
        self.listening = False
        modules.mic_stream_client.stop_streaming()
        self.status_label.config(text="Status: Idle")
        self.set_light_idle()
        self.log("Stopped listening.")

    def restart_penny(self):
        self.stop_listening()
        self.start_listening()
        self.log("Restarted Penny.")

    def listen_loop(self):
        while self.listening:
            if self.speech_queue.queue.qsize() > 0 or self.tts.is_speaking:
                time.sleep(0.5)
                continue

            self.set_light_listening()
            self.log("Recording 10s audio chunk...")
            audio_path = record_audio_chunk(duration=10)
            transcription = self.penny.transcribe(audio_path)

            if transcription:
                cleaned = transcription.strip()
                if cleaned == "" or cleaned.replace(".", "").strip() == "":
                    self.log("[Main] Ignored empty or invalid transcription.")
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    continue

                self.log(f"Transcribed: {cleaned}")
                self.set_light_thinking()

                response = self.penny.respond(cleaned)
                if response:
                    self.log(f"Penny: {response}")
                    safe_response = self.remove_emojis(response)

                    self.set_light_speaking()
                    if not self.muted:
                        self.speech_queue.add_to_queue(safe_response)
                    else:
                        self.log("[Mute] Penny is muted and did not speak.")

                    while self.speech_queue.queue.qsize() > 0 or self.tts.is_speaking:
                        time.sleep(0.2)

                    self.set_light_listening()

            if os.path.exists(audio_path):
                os.remove(audio_path)

    def update_server_status(self):
        try:
            main_response = requests.get("http://192.168.0.124:7001/ping", timeout=5)
            if main_response.status_code == 200:
                self.main_server_status.config(bg="green")
            else:
                self.main_server_status.config(bg="red")
        except:
            self.main_server_status.config(bg="red")

        try:
            secondary_response = requests.get("http://192.168.0.20:7001/ping", timeout=5)
            if secondary_response.status_code == 200:
                self.secondary_server_status.config(bg="green")
            else:
                self.secondary_server_status.config(bg="red")
        except:
            self.secondary_server_status.config(bg="red")

        # Schedule the next check after 15 seconds
        self.root.after(15000, self.update_server_status)

if __name__ == "__main__":
    root = tk.Tk()
    dashboard = PennyDashboard(root)
    def start_mic():
        modules.mic_stream_client.start_mic_listener(dashboard.speech_queue)
    mic_thread = threading.Thread(target=start_mic, daemon=True)
    mic_thread.start()

    root.mainloop()

