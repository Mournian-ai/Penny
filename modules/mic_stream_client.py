# modules/mic_stream_client.py

import asyncio
import websockets
import pyaudio
import requests

from modules.classify import classify_intent, detect_target, decide_action  # ✅ Import logic brain

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

speech_queue = None  # Optional reference from Penny

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
                    message = message.strip()

                    if not message or len(message.split()) < 2:
                        print("[CLIENT] Skipping empty or too-short input.")
                        continue

                    print(f"[PENNY HEARD] {message}")

                    # Run through classifier
                    intent = classify_intent(message)
                    target = detect_target(message)
                    action = decide_action(intent, target)

                    print(f"🔎 Intent: {intent} | 🎯 Target: {target} | 🛠 Action: {action}")

                    if "🧠" in action:
                        payload = {
                            "instruction": "Respond conversationally:",
                            "input": message
                        }
                        try:
                            response = requests.post(PENNY_API_URL, json=payload, timeout=10)
                            if response.status_code == 200:
                                output = response.json().get('output')
                                if speech_queue:
                                    speech_queue.add_to_queue(output)
                                else:
                                    print("[CLIENT] No speech_queue available, response not queued!")
                            else:
                                print(f"[CLIENT ERROR] Penny API response {response.status_code}: {response.text}")
                        except Exception as e:
                            print(f"[CLIENT ERROR] Penny API request failed: {e}")
                    else:
                        print("[CLIENT] 🛑 Not directed at Penny. Ignored.")

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
    speech_queue = queue_reference
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
    asyncio.run(send_audio())
