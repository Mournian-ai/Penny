# modules/mic_stream_client.py

import asyncio
import websockets
import pyaudio
import requests

# Settings
SERVER_URI = "ws://192.168.0.20:7001/ws/transcribe"  
PENNY_API_URL = "http://192.168.0.124:7001/respond"      

streaming_enabled = False  
websocket_connection = None

# Audio settings
CHUNK_DURATION_MS = 100
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)

# Question words for smarter detection
QUESTION_WORDS = ["who", "what", "when", "where", "why", "how", "can", "could", "would", "should",
                  "is", "are", "am", "do", "does", "did", "will", "shall", "have", "has", "may",
                  "might", "must"]

speech_queue = None  # This will be set if passed in by Penny's main program (not used yet!)

def is_question(text: str) -> bool:
    text = text.strip().lower()
    if text.endswith("?"):
        return True
    words = text.split()
    if not words:
        return False
    return words[0] in QUESTION_WORDS

async def send_audio():
    global websocket_connection
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)

    async with websockets.connect(SERVER_URI) as websocket:
        websocket_connection = websocket
        print("[CLIENT] Connected to server. Streaming audio...")

        async def receive():
            while True:
                try:
                    message = await websocket.recv()
                    print(f"[PENNY HEARD] {message}")

                    if is_question(message):
                        print("[CLIENT] Detected question, sending to Penny API...")
                        payload = {
                            "instruction": "Answer the following question briefly and conversationally.",
                            "input": message
                        }
                        try:
                            response = requests.post(PENNY_API_URL, json=payload, timeout=10)
                            if response.status_code == 200:
                                output = response.json().get('output')
                                print(f"[PENNY REPLY] {output}")

                                if speech_queue:
                                    speech_queue.add_to_queue(output)
                                else:
                                    print("[CLIENT] No speech_queue available, response not queued!")

                            else:
                                print(f"[CLIENT ERROR] Penny API response {response.status_code}: {response.text}")
                        except Exception as e:
                            print(f"[CLIENT ERROR] Penny API request failed: {e}")
                    else:
                        print("[CLIENT] Not a question, ignoring.")

                except websockets.ConnectionClosed:
                    print("[CLIENT] WebSocket closed by server.")
                    break

        asyncio.create_task(receive())

        try:
            while True:
                if streaming_enabled:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    await websocket.send(data)
                else:
                    # If not streaming, still read and discard mic data to avoid overflow
                    stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    await asyncio.sleep(CHUNK_DURATION_MS / 1000.0)
        except KeyboardInterrupt:
            print("[CLIENT] Stopping mic stream...")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

def start_mic_listener(queue_reference=None):
    global speech_queue
    speech_queue = queue_reference  # Optionally pass the real speech_queue later
    asyncio.run(send_audio())

def start_streaming():
    global streaming_enabled
    streaming_enabled = True
    print("[MIC STREAM] Streaming enabled.")

def stop_streaming():
    global streaming_enabled
    streaming_enabled = False
    print("[MIC STREAM] Streaming disabled.")

if __name__ == "__main__":
    # If you run it directly: standalone mode (no queue needed)
    asyncio.run(send_audio())
