import pickle
import difflib, os

MODEL_FILE = os.path.join(os.path.dirname(__file__), "model.pkl")

# Load model and vectorizer
with open(MODEL_FILE, "rb") as f:
    vectorizer, classifier = pickle.load(f)

def classify_intent(text):
    """Classify user input into intent."""
    X = vectorizer.transform([text])
    prediction = classifier.predict(X)[0]
    return prediction

def detect_target(text):
    """Detect if user is addressing Penny or someone else."""
    text = text.strip().lower()
    words = text.split()

    not_penny_keywords = ["chat", "guys", "everyone", "folks", "all", "myriad", "alex", "team", "stream", "yall"]
    penny_keywords = ["penny", "pennybot", "hey penny", "yo penny", "oi penny", "pen", "penpen"]

    # Direct match first
    for word in penny_keywords:
        if word in text:
            return "penny"

    for word in not_penny_keywords:
        if word in text:
            return "not_penny"

    # Fuzzy match: check each word against both lists
    for word in words:
        if difflib.get_close_matches(word, penny_keywords, n=1, cutoff=0.85):
            return "penny"
        if difflib.get_close_matches(word, not_penny_keywords, n=1, cutoff=0.85):
            return "not_penny"

    return "unknown"
def decide_action(intent, target):
    if target == "penny":
        return "🧠 Respond with LLM"
    elif target == "unknown":
        return "🧠 Respond with LLM (uncertain target)"
    else:
        return "🛑 Stay silent (user talking to someone else)"

if __name__ == "__main__":
    print("Penny Intent/Target Classifier 🧠")
    print("---------------------------------\n")
    
    while True:
        user_input = input("Say something: ").strip()
        if not user_input:
            continue

        intent = classify_intent(user_input)
        target = detect_target(user_input)
        action = decide_action(intent, target)

        print(f"\n🔎 Intent: {intent}")
        print(f"🎯 Target: {target}")
        print(f"🛠 Action: {action}\n")
        print("-" * 40)
