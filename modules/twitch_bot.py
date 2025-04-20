import threading
import time
import os
import asyncio
from dotenv import load_dotenv
from twitchio.ext import commands
import requests

from modules.cooldown_manager import CooldownManager

load_dotenv()

TWITCH_NICK = os.getenv("TWITCH_NICK")
TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")
FASTAPI_URL = os.getenv("FASTAPI_URL")

speech_queue = None 

class TwitchBot(commands.Bot):
    def __init__(self, speech_queue_ref):  # ✅ Add speech_queue_ref here
        super().__init__(token=TWITCH_TOKEN, prefix="!", initial_channels=[TWITCH_CHANNEL])
        self.should_stop = asyncio.Event()
        self.cooldown_manager = CooldownManager()
        self.speech_queue = speech_queue_ref

    async def event_ready(self):
        print(f"[TwitchBot] Connected as {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return

        username = message.author.name
        content = message.content
        print(f"[TwitchBot] {username}: {content}")

        if "penny" in content.lower():
            try:
                payload = {
                    "input": content,
                    "username": username
                }
                response = requests.post(f"{FASTAPI_URL}/respond_chat", json=payload)
                if response.status_code == 200:
                    reply = response.json().get("output", "")
                    self.speech_queue.add_to_queue(reply)
                else:
                    print(f"[TwitchBot] Respond error: {response.status_code}")
            except Exception as e:
                print(f"[TwitchBot] Error sending to respond: {e}")

    async def run_bot(self):
        await self.connect()
        await self.should_stop.wait()
        await self.close()

    async def event_usernotice(self, channel, tags):
        msg_id = tags.get('msg-id')
        username = tags.get('login') or "someone"
        amount = ""

        if msg_id == "submysterygift":
            if self.cooldown_manager.is_ready("mysterygift", 5):
                amount = tags.get('msg-param-mass-gift-count', "1")
                payload = {"event_type": "gift", "username": username, "amount": amount}
                await self.send_react_event(payload)

        elif msg_id == "subgift":
            if self.cooldown_manager.is_ready("subgift", 5):
                payload = {"event_type": "gift", "username": username, "amount": "1"}
                await self.send_react_event(payload)

        elif msg_id == "resub":
            amount = tags.get('msg-param-cumulative-months', "1")
            payload = {"event_type": "resub", "username": username, "amount": amount}
            await self.send_react_event(payload)

        elif msg_id == "raid":
            if self.cooldown_manager.is_ready("raid", 10):
                amount = tags.get('msg-param-viewerCount', "1")
                payload = {"event_type": "raid", "username": username, "amount": amount}
                await self.send_react_event(payload)
                await self.send_shoutout(username, amount)

    async def send_shoutout(self, username, viewer_count):
        try:
            payload = {"username": username, "viewer_count": viewer_count}
            response = requests.post(f"{FASTAPI_URL}/shoutout", json=payload)
            if response.status_code == 200:
                reply = response.json().get("output", "")
                self.speech_queue.add_to_queue(reply)
            else:
                print(f"[TwitchBot] Failed to hit /shoutout: {response.status_code}")
        except Exception as e:
            print(f"[TwitchBot] Error sending shoutout event: {e}")

    async def send_react_event(self, payload):
        try:
            response = requests.post(f"{FASTAPI_URL}/react_event", json=payload)
            if response.status_code == 200:
                reply = response.json().get("output", "")
                self.speech_queue.add_to_queue(reply)
            else:
                print(f"[TwitchBot] Failed to hit /react_event: {response.status_code}")
        except Exception as e:
            print(f"[TwitchBot] Error sending event: {e}")

bot = None

def start_twitch_bot(shared_speech_queue):
    global bot
    if bot is not None:
        print("[TwitchBot] Bot is already running.")
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = TwitchBot(shared_speech_queue)
    loop.run_until_complete(bot.run_bot())

def stop_twitch_bot():
    if bot:
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(bot.should_stop.set)

def launch_twitch_bot_thread(shared_speech_queue):
    def start():
        global bot
        if bot is not None:
            print("[TwitchBot] Bot is already running.")
            return
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot = TwitchBot(shared_speech_queue)  # pass it here too!
        loop.run_until_complete(bot.run_bot())

    twitch_thread = threading.Thread(target=start, daemon=True)
    twitch_thread.start()
    print("[Main] Twitch bot launched.")

