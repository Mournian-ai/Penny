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
                dropped = self.queue.get_nowait()
                print(f"[SpeechQueue] Dropped oldest: {dropped[:30]}...")
            except Exception:
                pass
        self.queue.put(text)

    def process_queue(self):
        while self.running:
            if not self.queue.empty():
                text = self.queue.get()
                print(f"[SpeechQueue] Speaking: {text}")
                if self.dashboard:
                    self.dashboard.log(f"[SpeechQueue] Speaking: {text}")
                self.tts.is_speaking = True
                self.tts.speak(text)
                self.tts.is_speaking = False
                time.sleep(1)
            else:
                time.sleep(0.1)

    def stop(self):
        self.running = False
