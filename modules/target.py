# target.py

import difflib

# This should eventually be updated live from Twitch
DYNAMIC_CHATTERS = ["myriad", "alex", "mournian", "chat", "everyone"]

PENNY_NAMES = [
    "penny", "hey penny", "yo penny", "oi penny", "pennybot", "pen",
    "penn", "pen pen", "penneth", "pennington"
]

def detect_target(text: str) -> str:
    text = text.strip().lower()

    # Direct call to Penny (keyword-based)
    if any(name in text for name in PENNY_NAMES):
        return "penny"

    # Split the sentence and check for close matches to chatter names
    words = text.split()
    for word in words:
        match = difflib.get_close_matches(word, DYNAMIC_CHATTERS, n=1, cutoff=0.85)
        if match:
            return "not_penny"

    # No known targets detected
    return "unknown"
