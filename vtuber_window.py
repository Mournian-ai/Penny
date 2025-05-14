import tkinter as tk
from PIL import Image, ImageTk
import ctypes
import os
import random
import sounddevice as sd
import numpy as np

def find_device(name_substring):
    for i, dev in enumerate(sd.query_devices()):
        if name_substring.lower() in dev['name'].lower() and dev['max_input_channels'] > 0:
            return i
    return None

VAC_DEVICE_INDEX = find_device("CABLE Output") 

def get_input_volume_stream(callback, samplerate=44100, blocksize=1024):
    def audio_callback(indata, frames, time, status):
        volume = np.linalg.norm(indata) * 10
        volume = min(max(volume, 0), 100)
        callback(volume)

    stream = sd.InputStream(
        device=VAC_DEVICE_INDEX,
        channels=1,
        samplerate=samplerate,
        blocksize=blocksize,
        callback=audio_callback
    )
    return stream
    
IMAGE_PATH = "penny_main.png"
SCALE_FACTOR = 0.5
EYE_OPEN_LEFT = "eye_open_left.png"
EYE_OPEN_RIGHT = "eye_open_right.png"
EYE_CLOSED_LEFT = "eye_close_left.png"
EYE_CLOSED_RIGHT = "eye_close_right.png"
MOUTH_IMAGE = "mouth.png"
LEFT_EYE_POS = (200, 245)
RIGHT_EYE_POS = (265, 245)

def make_window_transparent_and_clickthrough(window):
    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
    styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    styles |= 0x80000 | 0x20
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles)
    ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0x000000, 255, 0x01)

class VTuberWindow:
    def __init__(self, root):
        self.root = root
        # self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        # self.root.wm_attributes("-transparentcolor", "black")
        self.root.configure(bg="#00FF00")
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.mouth_x1 = 245
        self.mouth_y1 = 306
        self.mouth_width = 40
        self.volume_level = 0
        self.stream = get_input_volume_stream(self.set_volume)
        self.stream.start()
    
        base = Image.open(IMAGE_PATH)
        base = base.resize((int(base.width * SCALE_FACTOR), int(base.height * SCALE_FACTOR)), Image.Resampling.LANCZOS)
        base = base.convert("RGBA")
        base_data = base.getdata()
        base.putdata([(0, 0, 0, 0) if px[:3] == (0, 0, 0) else px for px in base_data])
        self.tk_image = ImageTk.PhotoImage(base)

        self.canvas = tk.Canvas(root, width=base.width, height=base.height, bg="#00FF00", highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        self.mouth_img_original = load_and_scale(MOUTH_IMAGE, scale=.15)  # You can tweak the scale
        self.mouth_img = self.mouth_img_original
        self.mouth = self.canvas.create_image(self.mouth_x1, self.mouth_y1, image=self.mouth_img, anchor=tk.CENTER)
        self.update_mouth()
        # Load all eye images
        self.eye_open_left = load_and_scale(EYE_OPEN_LEFT)
        self.eye_open_right = load_and_scale(EYE_OPEN_RIGHT)
        self.eye_closed_left = load_and_scale(EYE_CLOSED_LEFT)
        self.eye_closed_right = load_and_scale(EYE_CLOSED_RIGHT)
        self.offset_x = 0
        self.offset_y = 0
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        # Place open eyes
        self.left_eye = self.canvas.create_image(*LEFT_EYE_POS, image=self.eye_open_left, anchor=tk.NW)
        self.right_eye = self.canvas.create_image(*RIGHT_EYE_POS, image=self.eye_open_right, anchor=tk.NW)
        self.canvas.update() 
        # Start blinking
        self.schedule_blink()

        # Transparent click-through
        # make_window_transparent_and_clickthrough(root)
    def start_move(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def do_move(self, event):
        x = self.root.winfo_pointerx() - self.offset_x
        y = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f"+{x}+{y}")
    
    def set_volume(self, volume):
        self.volume_level = volume

    def blink(self):
    # Temporarily shift Y position for closed eyes
        self.canvas.itemconfigure(self.left_eye, image=self.eye_closed_left)
        self.canvas.itemconfigure(self.right_eye, image=self.eye_closed_right)
        
        # Optional: manually adjust their positions
        self.canvas.coords(self.left_eye, LEFT_EYE_POS[0], LEFT_EYE_POS[1] + 13)
        self.canvas.coords(self.right_eye, RIGHT_EYE_POS[0], RIGHT_EYE_POS[1] + 13)

        # Reset after short delay
        self.root.after(150, self.unblink)

        self.schedule_blink()
    def unblink(self):
        self.canvas.itemconfigure(self.left_eye, image=self.eye_open_left)
        self.canvas.itemconfigure(self.right_eye, image=self.eye_open_right)

        self.canvas.coords(self.left_eye, *LEFT_EYE_POS)
        self.canvas.coords(self.right_eye, *RIGHT_EYE_POS)

    def schedule_blink(self):
            self.root.after(random.randint(3000, 7000), self.blink)

    def update_mouth(self):
        mouth_scale_x = 1 + (self.volume_level / 250)
        mouth_scale_y = 1 + (self.volume_level / 100)

        # Add a small random bounce (±2% to ±5%)
        bounce_x = random.uniform(0.98, 1.02)
        bounce_y = random.uniform(0.95, 1.05)

        scaled_x = mouth_scale_x * bounce_x
        scaled_y = mouth_scale_y * bounce_y

        original_pil = Image.open(MOUTH_IMAGE)  # <-- we'll optimize this next
        new_width = int(self.mouth_img_original.width() * scaled_x)
        new_height = int(self.mouth_img_original.height() * scaled_y)

        resized_pil = original_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)

        self.mouth_img = ImageTk.PhotoImage(resized_pil)

        self.canvas.itemconfig(self.mouth, image=self.mouth_img)

        self.root.after(100, self.update_mouth)


    def move_mouth(self, dx, dy):
        self.mouth_x1 += dx
        self.mouth_y1 += dy
        print(f"New mouth position: x1={self.mouth_x1}, y1={self.mouth_y1}")

def load_and_scale(path, scale=0.05):  # ← Adjust scale as needed
    img = Image.open(path)
    new_size = (int(img.width * scale), int(img.height * scale))
    return ImageTk.PhotoImage(img.resize(new_size, Image.Resampling.NEAREST))

def launch_vtuber_window(master_root):
    vtuber_window = tk.Toplevel(master_root)
    vtuber_window.title("Penny VTuber")
    app = VTuberWindow(vtuber_window)
    return app

# if __name__ == "__main__":