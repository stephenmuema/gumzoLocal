import torch
import tkinter as tk
from tkinter import filedialog, ttk
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
import os
import subprocess
import threading

_MODELS = {
    "tiny.en": "Systran/faster-whisper-tiny.en",
    "tiny": "Systran/faster-whisper-tiny",
    "base.en": "Systran/faster-whisper-base.en",
    "base": "Systran/faster-whisper-base",
    "small.en": "Systran/faster-whisper-small.en",
    "small": "Systran/faster-whisper-small",
    "medium.en": "Systran/faster-whisper-medium.en",
    "medium": "Systran/faster-whisper-medium",
    "large-v1": "Systran/faster-whisper-large-v1",
    "large-v2": "Systran/faster-whisper-large-v2",
    "large-v3": "Systran/faster-whisper-large-v3",
    "large": "Systran/faster-whisper-large-v3",
    "distil-large-v2": "Systran/faster-distil-whisper-large-v2",
    "distil-medium.en": "Systran/faster-distil-whisper-medium.en",
    "distil-small.en": "Systran/faster-distil-whisper-small.en",
    "distil-large-v3": "Systran/faster-distil-whisper-large-v3",
    "large-v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    "turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
}

FRIENDLY_MODEL_NAMES = {
    "tiny.en": "Nano (English Only)",
    "tiny": "Nano Multilingual",
    "base.en": "Basic (English Only)",
    "base": "Basic Multilingual",
    "small.en": "Micro (English Only)",
    "small": "Micro Multilingual",
    "medium.en": "Milli (English Only)",
    "medium": "Milli Multilingual",
    "large-v1": "Main Version One Multilingual",
    "large-v2": "Main Version Two Multilingual",
    "large-v3": "Main version Three Multilingual",
    "large": "Main Normal Multilingual",
    "distil-large-v2": "Distilled Main Version Two Multilingual",
    "distil-medium.en": "Distilled Milli (English Only) Multilingual",
    "distil-small.en": "Distilled Micro (English Only) ",
    "distil-large-v3": "Distilled Main Version Three Multilingual",
    "large-v3-turbo": "Main Version Three Flash Multilingual",
    "turbo": "Flash Multilingual"
}


def get_model_path(model_size):
    home_dir = os.path.expanduser("~")
    model_dir = os.path.join(home_dir, "gumzo")
    os.makedirs(model_dir, exist_ok=True)
    return os.path.join(model_dir, model_size)


def download_model(model_size):
    model_path = get_model_path(model_size)
    if not os.path.exists(model_path):
        progress_label.config(text=f"Downloading {FRIENDLY_MODEL_NAMES[model_size]} model...")
        root.update_idletasks()
        model = WhisperModel(_MODELS[model_size], download_root=model_path)
        progress_label.config(text=f"{FRIENDLY_MODEL_NAMES[model_size]} model downloaded successfully.")
    return model_path


def transcribe_and_translate(file_path, model_size, target_lang=None):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_path = download_model(model_size)
    model = WhisperModel(_MODELS[model_size], device=device, compute_type="float16", download_root=model_path)

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
    model_size = model_var.get()
    target_lang = lang_var.get()

    if not file_path:
        result_text.set("Please select an audio or video file.")
        return

    progress_label.config(text=f"Processing with {FRIENDLY_MODEL_NAMES[model_size]} model...")
    root.update_idletasks()

    def run_transcription():
        transcription, translation = transcribe_and_translate(file_path, model_size,
                                                              target_lang if target_lang != "None" else None)
        result_text.set(f"Transcription:\n{transcription}\n\nTranslation:\n{translation if translation else 'N/A'}")
        progress_label.config(text="Done.")

    threading.Thread(target=run_transcription, daemon=True).start()


# GUI Setup
root = tk.Tk()
root.title("Transcription and Translation App")
root.geometry("650x500")
root.configure(bg="#f0f0f0")

frame = tk.Frame(root, bg="#f0f0f0")
frame.pack(pady=20)

entry_file_path = ttk.Entry(frame, width=50)
entry_file_path.pack(side=tk.LEFT, padx=5)
btn_browse = ttk.Button(frame, text="Browse", command=browse_file)
btn_browse.pack(side=tk.LEFT)

model_var = tk.StringVar(value="medium")
model_names = list(FRIENDLY_MODEL_NAMES.keys())
dropdown_model = ttk.Combobox(root, textvariable=model_var, values=[FRIENDLY_MODEL_NAMES[m] for m in model_names],
                              state="readonly")
dropdown_model.pack(pady=10)
dropdown_model.current(model_names.index("medium"))

lang_var = tk.StringVar(value="None")
languages = ["None", "en", "fr", "es", "de", "zh", "ar", "ru"]
dropdown_lang = ttk.Combobox(root, textvariable=lang_var, values=languages, state="readonly")
dropdown_lang.pack(pady=10)
dropdown_lang.current(0)

btn_process = ttk.Button(root, text="Transcribe & Translate", command=process_media)
btn_process.pack(pady=10)

progress_label = ttk.Label(root, text="", background="#f0f0f0")
progress_label.pack(pady=5)

result_text = tk.StringVar()
result_label = ttk.Label(root, textvariable=result_text, wraplength=600, justify="left", background="#ffffff",
                         relief="solid", padding=10)
result_label.pack(pady=10, padx=10, fill="both")

root.mainloop()