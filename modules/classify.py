import pickle
import difflib, os, time
from rapidfuzz import fuzz  # If you're already using this instead of difflib

MODEL_FILE = os.path.join(os.path.dirname(__file__), "model.pkl")
last_target = None
last_target_time = 0
CONTEXT_TIMEOUT = 15  # seconds
CHATTER_LIST = []

PENNY_NAMES = [
    "penny", "hey penny", "yo penny", "oi penny", "pennybot", "pen",
    "penn", "pen pen", "penneth", "pennington"
]

# Load model and vectorizer
with open(MODEL_FILE, "rb") as f:
    vectorizer, classifier = pickle.load(f)

def classify_intent(text):
    X = vectorizer.transform([text])
    return classifier.predict(X)[0]

def detect_target(text: str):
    global last_target, last_target_time
    text = text.strip().lower()
    current_time = time.time()

    # ✅ Direct Penny references
    if any(name in text for name in PENNY_NAMES):
        last_target = "penny"
        last_target_time = current_time
        return "penny"

    # ✅ Match to known chatters
    for chatter in CHATTER_LIST:
        if fuzz.partial_ratio(text, chatter.lower()) > 85:
            last_target = "not_penny"
            last_target_time = current_time
            return "not_penny"

    # ✅ Use recent target context if still fresh
    if last_target and (current_time - last_target_time < CONTEXT_TIMEOUT):
        return "penny_context" if last_target == "penny" else "not_penny"

    return "unknown"

def decide_action(intent, target):
    if target in ("penny", "penny_context"):
        return "🧠 Respond with LLM"
    elif target == "unknown":
        if intent in ("question", "reaction"):
            return "🧠 Respond with LLM (uncertain target)"
        else:
            return "🛑 Stay silent (uncertain)"
    else:
        return "🛑 Stay silent (user talking to someone else)"