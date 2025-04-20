import tkinter as tk
from tkinter import messagebox, simpledialog
import chromadb
import requests

# Connect to Penny's FastAPI
BASE_URL = "http://192.168.0.124:7001"

class MemoryBrowser(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Penny Memory Manager")
        self.configure(bg="black")
        self.geometry("1000x700")

        self.search_entry = tk.Entry(self, font=("Consolas", 14), bg="black", fg="white", insertbackground="white")
        self.search_entry.pack(pady=10)
        
        search_button = tk.Button(self, text="Search", command=self.search, bg="purple", fg="white", font=("Consolas", 12))
        search_button.pack(pady=5)

        self.memory_list = tk.Listbox(self, bg="black", fg="violet", font=("Consolas", 12), width=140)
        self.memory_list.pack(pady=10, padx=10, fill="both", expand=True)
        self.memory_list.bind("<Double-Button-1>", self.view_full_memory)

        button_frame = tk.Frame(self, bg="black")
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Add Memory", command=self.add_memory, bg="green", fg="black", font=("Consolas", 10)).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Refresh", command=self.refresh, bg="blue", fg="white", font=("Consolas", 10)).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Exit", command=self.destroy, bg="gray", fg="black", font=("Consolas", 10)).grid(row=0, column=2, padx=5)

        self.refresh()

    def refresh(self):
        self.memory_list.delete(0, tk.END)
        try:
            response = requests.post(f"{BASE_URL}/memory/query", json={"query": " ", "top_k": 200})
            data = response.json()
            self.entries = data.get("matches", [])
            for entry in self.entries:
                category = entry['category']
                text = entry['text'][:100].replace("\n", " ") + "..."
                self.memory_list.insert(tk.END, f"({category}) {text}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load memories:\n{e}")

    def search(self):
        query = self.search_entry.get()
        if not query.strip():
            self.refresh()
            return
        self.memory_list.delete(0, tk.END)
        try:
            response = requests.post(f"{BASE_URL}/memory/query", json={"query": query, "top_k": 20})
            data = response.json()
            self.entries = data.get("matches", [])
            for entry in self.entries:
                category = entry['category']
                text = entry['text'][:100].replace("\n", " ") + "..."
                self.memory_list.insert(tk.END, f"({category}) {text}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search memories:\n{e}")

    def add_memory(self):
        text = simpledialog.askstring("New Memory", "Enter memory text:")
        if text:
            category = simpledialog.askstring("Category", "Enter category (e.g., about_mournian, schedule1_real):")
            if not category:
                category = "general"
            try:
                response = requests.post(f"{BASE_URL}/memory/store", json={
                    "text": text,
                    "category": category
                })
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Memory stored successfully!")
                    self.refresh()
                else:
                    messagebox.showerror("Error", f"Failed to store memory:\n{response.text}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to store memory:\n{e}")

    def view_full_memory(self, event):
        selected = self.memory_list.curselection()
        if selected:
            index = selected[0]
            full_text = self.entries[index]['text']

            top = tk.Toplevel(self)
            top.title("Full Memory View")
            top.configure(bg="black")
            top.geometry("800x500")

            text_area = tk.Text(top, wrap="word", font=("Consolas", 12), bg="black", fg="violet", insertbackground="white")
            text_area.insert(tk.END, full_text)
            text_area.config(state="disabled")  # Make it readonly
            text_area.pack(expand=True, fill="both", padx=10, pady=10)

if __name__ == "__main__":
    app = MemoryBrowser()
    app.mainloop()
