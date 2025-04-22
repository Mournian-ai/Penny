import pickle

MODEL_FILE = "model.pkl"

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

    not_penny_keywords = ["chat", "guys", "everyone", "folks", "all", "myriad", "alex", "team", "stream", "yall"]
    penny_keywords = ["penny", "pennybot", "hey penny", "yo penny", "oi penny"]

    for word in penny_keywords:
        if word in text:
            return "penny"

    for word in not_penny_keywords:
        if word in text:
            return "not_penny"

    return "unknown"

def decide_action(intent, target):
    """Decide how Penny should react."""
    if target == "not_penny":
        return "🛑 Stay silent (user talking to someone else)"

    if intent == "question":
        return "🧠 Answer thoughtfully (LLM)"
    elif intent == "reaction":
        return "😊 React casually (short reply)"
    elif intent == "statement":
        return "🤔 Maybe ignore or random casual comment"
    elif intent == "chatter":
        return "🛑 Stay silent (user talking to chat)"
    else:
        return "❓ Unknown action"

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
