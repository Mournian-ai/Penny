import requests
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io

# ====== CONFIG ======
API_TOKEN = '28803dc42470fd4ecbc3c8cda2e0e50f9eea3f64'
COUNTRY = 'US'
# =====================

def fetch_image(url):
    """Download and return a PIL Image from URL."""
    try:
        response = requests.get(url)
        img_data = response.content
        image = Image.open(io.BytesIO(img_data))
        return image
    except Exception as e:
        print(f"Error loading box art: {e}")
        return None

def search_game(game_name):
    """Use ITAD search API to find games."""
    search_url = 'https://api.isthereanydeal.com/games/search/v1'
    params = {
        'key': API_TOKEN,
        'title': game_name,
        'results': 5
    }
    try:
        response = requests.get(search_url, params=params)
        print(f"DEBUG status code: {response.status_code}")
        print(f"DEBUG raw text: {response.text}")
        data = response.json()
    except Exception as e:
        print(f"Error contacting ITAD search API: {e}")
        return None

    if not data or not isinstance(data, list):
        print(f"No search results found for '{game_name}'.")
        return None

    return data

def choose_game(results):
    """Let user pick one game if multiple results."""
    print("\nFound multiple games:")
    for idx, game in enumerate(results):
        print(f"[{idx + 1}] {game.get('title', 'Unknown Title')}")

    while True:
        choice = input("\nPick a number (or press Enter to cancel): ").strip()
        if not choice:
            return None
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(results):
                return results[choice - 1]
        print("Invalid choice. Try again.")

def get_prices_v3(game_ids):
    """Fetch live prices using v3 POST API."""
    url = "https://api.isthereanydeal.com/games/prices/v3"
    headers = {
        'Content-Type': 'application/json'
    }
    params = {
        'key': API_TOKEN,
        'country': COUNTRY
    }
    try:
        response = requests.post(url, params=params, headers=headers, data=json.dumps(game_ids))
        print(f"DEBUG status code (price): {response.status_code}")
        print(f"DEBUG raw text (price): {response.text}")
        data = response.json()
    except Exception as e:
        print(f"Error contacting ITAD price API: {e}")
        return None

    if not data:
        print("No pricing data found.")
        return None

    return data

def display_prices(game_title, price_data, history_low=None, boxart_url=None):
    """Pop up a Tkinter window showing the prices."""
    window = tk.Tk()
    window.title(f"Prices for {game_title}")
    window.configure(bg="#1a001a")  # Dark purple background
    window.geometry("750x900")

    # Load and display box art
    if boxart_url:
        image = fetch_image(boxart_url)
        if image:
            image = image.resize((300, 300))
            photo = ImageTk.PhotoImage(image)
            img_label = tk.Label(window, image=photo, bg="#1a001a")
            img_label.image = photo
            img_label.pack(pady=10)

    title_label = tk.Label(window, text=game_title, font=("Consolas", 20, "bold"), fg="#cc99ff", bg="#1a001a")
    title_label.pack(pady=10)

    frame = tk.Frame(window, bg="#1a001a")
    frame.pack(pady=10, fill="both", expand=True)

    scrollbar = ttk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    text = tk.Text(
        frame,
        yscrollcommand=scrollbar.set,
        bg="#1a001a",
        fg="white",
        font=("Consolas", 12),
        wrap="word",
        relief="flat",
        selectbackground="#663399"
    )
    text.pack(fill="both", expand=True)

    scrollbar.config(command=text.yview)

    if history_low:
        low_price = history_low.get('all', {}).get('amount', None)
        if low_price:
            text.insert("end", f"Historical Lowest Price: ${low_price:.2f}\n\n", "lowprice")

    wanted_stores = {"Steam", "Epic Games Store", "Humble Store"}

    # Build best offers
    best_prices = {}
    for entry in price_data:
        store_name = entry['shop']['name']
        price_info = entry['price']
        regular_info = entry['regular']
        url = entry['url']

        if store_name not in best_prices:
            best_prices[store_name] = {
                "current_price": price_info['amount'],
                "original_price": regular_info['amount'],
                "discount": entry.get('cut', 0),
                "url": url
            }

    found_any = False

    for store in wanted_stores:
        if store in best_prices:
            info = best_prices[store]
            found_any = True
            text.insert("end", f"{store}\n", ("store",))
            text.insert("end", f"  Price: ${info['current_price']:.2f} (was ${info['original_price']:.2f})\n", ("normal",))
            text.insert("end", f"  Discount: {info['discount']}% off\n", ("normal",))
            text.insert("end", f"  Link: {info['url']}\n\n", ("normal",))

    if not found_any:
        text.insert("end", "No offers found on Steam, Epic, or Humble.\n", ("normal",))

    text.tag_config("store", foreground="#cc99ff", font=("Consolas", 14, "bold"))
    text.tag_config("normal", foreground="white")
    text.tag_config("lowprice", foreground="gold", font=("Consolas", 13, "bold"))

    text.config(state="disabled")
    window.after(15000, window.destroy)
    window.mainloop()

def main():
    raw_game_name = input("Enter the name of the game: ").strip()

    results = search_game(raw_game_name)
    if not results:
        return

    if len(results) == 1:
        game = results[0]
    else:
        game = choose_game(results)
    
    if not game:
        print("Cancelled.")
        return

    print("\nSelected Game Info:")
    print(f"Title: {game['title']}")
    print(f"Slug: {game['slug']}")
    print(f"ID: {game['id']}")

    boxart_url = game.get('assets', {}).get('boxart')

    prices_data = get_prices_v3([game['id']])
    if not prices_data:
        print("No price data available.")
        return

    if isinstance(prices_data, list) and prices_data:
        first_game = prices_data[0]
    else:
        print("Unexpected price data format.")
        return

    deals = first_game.get('deals', [])
    history_low = first_game.get('historyLow', None)

    if not deals:
        print("No active deals found.")
        return

    display_prices(game['title'], deals, history_low, boxart_url)

if __name__ == "__main__":
    main()
