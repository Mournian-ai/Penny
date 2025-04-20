import time

class CooldownManager:
    def __init__(self):
        self.cooldowns = {}

    def is_ready(self, key: str, cooldown_seconds: float) -> bool:
        """
        Check if a certain event type (key) is ready to be triggered again.
        """
        now = time.time()
        last_time = self.cooldowns.get(key, 0)
        if now - last_time >= cooldown_seconds:
            self.cooldowns[key] = now
            return True
        return False

    def force_reset(self, key: str):
        """
        Force reset the cooldown for a given key immediately.
        """
        self.cooldowns[key] = time.time()