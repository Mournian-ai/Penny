import json
import requests
import time

# Config
SERVER_URL = "http://192.168.0.124:7001/memory/store"
INPUT_JSONL = "memories.jsonl"

def upload_memories(jsonl_file):
    """Upload memories from a JSONL file to Penny's memory API."""
    try:
        with open(jsonl_file, "r", encoding="utf-8") as infile:
            lines = infile.readlines()

        if not lines:
            print("❌ No memories found to upload.")
            return

        for idx, line in enumerate(lines, start=1):
            try:
                memory = json.loads(line)
                payload = {
                    "text": memory["memory"],
                    "category": memory.get("category", "general"),
                    "source": memory.get("source", "manual")
                }

                response = requests.post(SERVER_URL, json=payload)

                if response.status_code == 200:
                    print(f"[{idx}] ✅ Uploaded: {payload['text'][:40]}...")
                else:
                    print(f"[{idx}] ❌ Failed ({response.status_code}): {response.text}")

                time.sleep(0.05)  # Small delay to avoid spamming server

            except Exception as inner_e:
                print(f"[{idx}] ❌ Failed to process memory: {inner_e}")

        print(f"✅ Finished uploading {len(lines)} memories.")

    except Exception as e:
        print(f"❌ Error reading JSONL: {e}")

if __name__ == "__main__":
    upload_memories(INPUT_JSONL)
