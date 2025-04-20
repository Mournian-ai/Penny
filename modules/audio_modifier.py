import tkinter as tk
from tkinter import filedialog
from pydub import AudioSegment
from pydub.playback import play

def modify_audio(input_path, speed=1.05, semitones=-1):
    audio = AudioSegment.from_file(input_path)

    # Speed adjustment
    new_frame_rate = int(audio.frame_rate * speed)
    audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})

    # Pitch adjustment
    octaves = semitones / 12.0
    new_sample_rate = int(audio.frame_rate * (2.0 ** octaves))
    audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})

    # Resample back to standard
    audio = audio.set_frame_rate(16000)
    return audio

def launch_modifier_gui():
    root = tk.Tk()
    root.title("Penny Audio Modifier")

    file_path = tk.StringVar()
    speed_var = tk.DoubleVar(value=1.05)
    pitch_var = tk.DoubleVar(value=-1)

    def browse_file():
        path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        file_path.set(path)

    def play_modified():
        path = file_path.get()
        if not path:
            print("No file selected.")
            return

        speed = speed_var.get()
        semitones = pitch_var.get()

        print(f"[AudioModifier] Playing with speed {speed} and pitch {semitones} semitones.")
        modified = modify_audio(path, speed=speed, semitones=semitones)
        play(modified)

    # Layout
    tk.Label(root, text="WAV File:").pack()
    tk.Entry(root, textvariable=file_path, width=50).pack()
    tk.Button(root, text="Browse", command=browse_file).pack(pady=5)

    tk.Label(root, text="Speed (e.g., 1.05 = 5% faster):").pack()
    tk.Entry(root, textvariable=speed_var).pack()

    tk.Label(root, text="Pitch Shift (semitones, e.g., -1 lower):").pack()
    tk.Entry(root, textvariable=pitch_var).pack()

    tk.Button(root, text="Play Modified Audio", command=play_modified).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    launch_modifier_gui()