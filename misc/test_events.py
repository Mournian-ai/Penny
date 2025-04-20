import requests
from modules.speech_queue import SpeechQueue
import time

FASTAPI_URL = "http://192.168.0.124:7001"  # Change if needed
speech_queue = SpeechQueue()

def send_react_event(event_type, username="tester", amount=""):
    payload = {
        "event_type": event_type,
        "username": username,
        "amount": amount
    }
    try:
        response = requests.post(f"{FASTAPI_URL}/react_event", json=payload)
        if response.status_code == 200:
            reply = response.json().get("output", "")
            print(f"[TestEvents] Penny would say: {reply}")
            speech_queue.add_to_queue(reply)
        else:
            print(f"[TestEvents] Error hitting /react_event: {response.status_code}")
    except Exception as e:
        print(f"[TestEvents] Error: {e}")

def send_shoutout(username, viewer_count):
    payload = {
        "username": username,
        "viewer_count": viewer_count
    }
    try:
        response = requests.post(f"{FASTAPI_URL}/shoutout", json=payload)
        if response.status_code == 200:
            reply = response.json().get("output", "")
            print(f"[TestEvents] Penny would shoutout: {reply}")
            speech_queue.add_to_queue(reply)
        else:
            print(f"[TestEvents] Error hitting /shoutout: {response.status_code}")
    except Exception as e:
        print(f"[TestEvents] Error: {e}")

def main():
    while True:
        print("\n=== Penny Event Tester ===")
        print("1. Test Sub")
        print("2. Test Gifted Sub")
        print("3. Test Bits")
        print("4. Test Raid (with shoutout)")
        print("5. Test Follow")
        print("6. Exit")
        choice = input("Choose an event to test (1-6): ")

        if choice == "1":
            send_react_event(event_type="sub", username="mournian")
        elif choice == "2":
            send_react_event(event_type="gift", username="mournian", amount="5")
        elif choice == "3":
            amount = input("Enter bits amount: ")
            send_react_event(event_type="bits", username="mournian", amount=amount)
        elif choice == "4":
            send_react_event(event_type="raid", username="mournian", amount="25")
            time.sleep(1)  # Short delay before shoutout
            send_shoutout(username="mournian", viewer_count="25")
        elif choice == "5":
            send_react_event(event_type="follow", username="mournian")
        elif choice == "6":
            print("Goodbye!")
            speech_queue.stop()
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
