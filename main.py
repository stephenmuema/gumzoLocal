import torch
import tkinter as tk
from tkinter import filedialog, ttk
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
import os
import subprocess


def transcribe_and_translate(file_path, model_size="tiny", target_lang=None):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = WhisperModel(model_size, device=device,)

    # Convert video to audio if necessary
    if file_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
        audio_path = file_path.rsplit(".", 1)[0] + ".wav"
        subprocess.run(["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", audio_path, "-y"], check=True)
    else:
        audio_path = file_path

    segments, info = model.transcribe(audio_path)
    print(f"Detected language: {info.language}")

    full_transcription = "".join(segment.text + " " for segment in segments).strip()

    translated_text = None
    if target_lang:
        translated_text = GoogleTranslator(source="auto", target=target_lang).translate(full_transcription)

    return full_transcription, translated_text


def browse_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Media Files", "*.wav;*.mp3;*.ogg;*.m4a;*.mp4;*.mkv;*.avi;*.mov")])
    if file_path:
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(0, file_path)


def process_media():
    file_path = entry_file_path.get()
    target_lang = lang_var.get()

    if not file_path:
        result_text.set("Please select an audio or video file.")
        return

    transcription, translation = transcribe_and_translate(file_path, "medium",
                                                          target_lang if target_lang != "None" else None)

    result_text.set(f"Transcription:\n{transcription}\n\nTranslation:\n{translation if translation else 'N/A'}")


# GUI Setup
root = tk.Tk()
root.title("Transcription and Translation App")
root.geometry("650x450")
root.configure(bg="#f0f0f0")

frame = tk.Frame(root, bg="#f0f0f0")
frame.pack(pady=20)

entry_file_path = ttk.Entry(frame, width=50)
entry_file_path.pack(side=tk.LEFT, padx=5)
btn_browse = ttk.Button(frame, text="Browse", command=browse_file)
btn_browse.pack(side=tk.LEFT)

lang_var = tk.StringVar(value="None")
languages = ["None", "en", "fr", "es", "de", "zh", "ar", "ru"]  # Extend as needed
dropdown_lang = ttk.Combobox(root, textvariable=lang_var, values=languages, state="readonly")
dropdown_lang.pack(pady=10)
dropdown_lang.current(0)

btn_process = ttk.Button(root, text="Transcribe & Translate", command=process_media)
btn_process.pack(pady=10)

result_text = tk.StringVar()
result_label = ttk.Label(root, textvariable=result_text, wraplength=600, justify="left", background="#ffffff",
                         relief="solid", padding=10)
result_label.pack(pady=10, padx=10, fill="both")

root.mainloop()
