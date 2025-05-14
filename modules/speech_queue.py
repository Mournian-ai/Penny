import threading
import time
from queue import Queue

class SpeechQueue:
    def __init__(self, tts, dashboard_ref=None):
        self.tts = tts
        self.queue = Queue()
        self.running = True
        self.thread = threading.Thread(target=self.process_queue, daemon=True)
        self.thread.start()
        self.dashboard = dashboard_ref

    def add_to_queue(self, text):
        MAX_QUEUE_SIZE = 10
        if self.queue.qsize() >= MAX_QUEUE_SIZE:
            try:
                dropped, _ = self.queue.get_nowait()
                print(f"[SpeechQueue] Dropped oldest (queue full): {dropped[:30]}...")
            except Exception:
                pass
        # Store a tuple: (text, timestamp)
        self.queue.put((text, time.time()))

    def process_queue(self):
        EXPIRATION_TIME = 10  # seconds
        while self.running:
            if not self.queue.empty():
                # 🛑 Wait until not currently speaking
                while self.tts.is_speaking:
                    time.sleep(0.1)

                text, timestamp = self.queue.get()

                # Check expiration
                if time.time() - timestamp > EXPIRATION_TIME:
                    print(f"[SpeechQueue] Dropped expired message: {text[:30]}...")
                    if self.dashboard:
                        self.dashboard.log(f"[SpeechQueue] Dropped expired message: {text[:30]}...")
                    continue  # Skip speaking this one

                print(f"[SpeechQueue] Speaking: {text}")
                if self.dashboard:
                    self.dashboard.log(f"[SpeechQueue] Speaking: {text}")

                try:
                    self.tts.speak(text)
                except Exception as e:
                    print(f"[SpeechQueue] Error during speaking: {e}")
                    if self.dashboard:
                        self.dashboard.log(f"[SpeechQueue] Error during speaking: {e}")

                time.sleep(1)  # natural gap after speaking
            else:
                time.sleep(0.1)

    def stop(self):
        self.running = False
