import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Paths
DATASET_FILE = "dataset.jsonl"
MODEL_FILE = "model.pkl"

# Load dataset
texts = []
labels = []

with open(DATASET_FILE, "r", encoding="utf-8") as f:
    for line in f:
        entry = json.loads(line)
        texts.append(entry["text"])
        labels.append(entry["label"])

# Vectorize the text
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

# Train classifier
classifier = LogisticRegression(max_iter=1000)
classifier.fit(X, labels)

# Save model and vectorizer
with open(MODEL_FILE, "wb") as f:
    pickle.dump((vectorizer, classifier), f)

print(f"✅ Model trained and saved to {MODEL_FILE}")
