# modules/mic_stream_client.py

import asyncio
import websockets
import pyaudio
import requests
import traceback

from modules.classify import classify_intent, detect_target, decide_action

SERVER_URI = "ws://192.168.0.20:7001/ws/transcribe"
PENNY_API_URL = "http://192.168.0.124:7001/respond"

streaming_enabled = False
websocket_connection = None
speech_queue = None
stream_task = None

# Audio settings
CHUNK_DURATION_MS = 100
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)

async def audio_stream_loop(websocket, stream):
    try:
        while True:
            if streaming_enabled:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                await websocket.send(data)
            else:
                stream.read(CHUNK_SIZE, exception_on_overflow=False)
                await asyncio.sleep(CHUNK_DURATION_MS / 1000.0)
    except Exception as e:
        print(f"[CLIENT ERROR] Audio stream error: {e}")
        traceback.print_exc()

async def receive_loop(websocket):
    try:
        while True:
            message = await websocket.recv()
            message = message.strip()

            if not message or len(message.split()) < 2 or all(c in ".!?, " for c in message.lower()):
                print("[CLIENT] Skipping empty or too-short input.")
                continue

            print(f"[PENNY HEARD] {message}")

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
                            print("[CLIENT] No speech_queue available.")
                    else:
                        print(f"[CLIENT ERROR] LLM API: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"[CLIENT ERROR] LLM request failed: {e}")
    except websockets.ConnectionClosed as e:
        print(f"[CLIENT] WebSocket closed: {e.code} - {e.reason}")
    except Exception as e:
        print(f"[CLIENT ERROR] Receive loop failed: {e}")
        traceback.print_exc()

async def send_audio():
    global websocket_connection
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK_SIZE)

    try:
        print("[CLIENT] Connecting to websocket...")
        websocket_connection = await websockets.connect(SERVER_URI)
        print("[CLIENT] WebSocket connection established.")

        await asyncio.gather(
            receive_loop(websocket_connection),
            audio_stream_loop(websocket_connection, stream)
        )
    except Exception as e:
        print(f"[CLIENT ERROR] Main loop error: {e}")
        traceback.print_exc()
    finally:
        print("[CLIENT] Closing audio stream and terminating PyAudio.")
        stream.stop_stream()
        stream.close()
        p.terminate()
        if websocket_connection:
            await websocket_connection.close()

def start_mic_listener(queue_reference=None):
    global speech_queue, stream_task
    speech_queue = queue_reference
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stream_task = loop.create_task(send_audio())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("[CLIENT] Listener stopped.")
    finally:
        loop.close()

def start_streaming():
    global streaming_enabled
    streaming_enabled = True
    print("[MIC STREAM] Streaming enabled.")

def stop_streaming():
    global streaming_enabled
    streaming_enabled = False
    print("[MIC STREAM] Streaming disabled.")
