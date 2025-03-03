import torch
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
import os
import subprocess
import threading
from tkinter import messagebox
import customtkinter as ctk

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class GumzoAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Gumzo AI - Speech Transcription & Translation")
        self.geometry("800x600")

        # Variables
        self.file_path = ""
        self.model_var = tk.StringVar(value="Gumzo AI Standard")
        self.model_language_var = tk.StringVar(value="All Languages")
        self.lang_var = tk.StringVar(value="None")
        self.processing = False

        # Define model mappings
        self._MODELS = {
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
            "turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
        }

        # Create friendly name to model mapping
        self.model_friendly_names = {
            "Gumzo AI Basic (Tiny)": "tiny",
            "Gumzo AI Basic (English Only)": "tiny.en",
            "Gumzo AI Starter (Base)": "base",
            "Gumzo AI Starter (English Only)": "base.en",
            "Gumzo AI Standard (Small)": "small",
            "Gumzo AI Standard (English Only)": "small.en",
            "Gumzo AI Premium (Medium)": "medium",
            "Gumzo AI Premium (English Only)": "medium.en",
            "Gumzo AI Pro (v1)": "large-v1",
            "Gumzo AI Pro (v2)": "large-v2",
            "Gumzo AI Pro (v3)": "large-v3",
            "Gumzo AI Pro (Distilled v2)": "distil-large-v2",
            "Gumzo AI Pro (Distilled v3)": "distil-large-v3",
            "Gumzo AI Lite (Distilled Medium - English)": "distil-medium.en",
            "Gumzo AI Lite (Distilled Small - English)": "distil-small.en",
            "Gumzo AI Flash (v3 Flash)": "large-v3-turbo"
        }

        # Create UI elements
        self.create_ui()

    def create_ui(self):
        # Main frame with padding
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # App title and description
        title_label = ctk.CTkLabel(main_frame, text="Gumzo AI Transcription",
                                   font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(0, 10))

        description = ctk.CTkLabel(main_frame,
                                   text="Convert speech to text and translate to different languages",
                                   font=ctk.CTkFont(size=14))
        description.pack(pady=(0, 20))

        # File selection frame
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.pack(padx=10, pady=10, fill="x")

        file_label = ctk.CTkLabel(file_frame, text="Audio/Video File:")
        file_label.pack(side="left", padx=(10, 5))

        self.entry_file_path = ctk.CTkEntry(file_frame, width=400)
        self.entry_file_path.pack(side="left", padx=5, fill="x", expand=True)

        browse_btn = ctk.CTkButton(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side="left", padx=5)

        # Settings frame
        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.pack(padx=10, pady=10, fill="x")

        # Model selection
        model_label = ctk.CTkLabel(settings_frame, text="Model:")
        model_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        models = list(self.model_friendly_names.keys())
        models.sort()  # Sort alphabetically

        # Group models by category for the dropdown
        basic_models = [m for m in models if "Basic" in m]
        starter_models = [m for m in models if "Starter" in m]
        standard_models = [m for m in models if "Standard" in m]
        premium_models = [m for m in models if "Premium" in m]
        pro_models = [m for m in models if "Pro" in m]
        lite_models = [m for m in models if "Lite" in m]
        turbo_models = [m for m in models if "Turbo" in m]

        # Combine in logical order
        ordered_models = basic_models + starter_models + standard_models + premium_models + lite_models + pro_models + turbo_models

        model_dropdown = ctk.CTkOptionMenu(settings_frame, variable=self.model_var, values=ordered_models, width=300)
        model_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Language selection
        lang_label = ctk.CTkLabel(settings_frame, text="Translate to:")
        lang_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        languages = [
            "None",
            "English (en)",
            "French (fr)",
            "Spanish (es)",
            "German (de)",
            "Chinese (zh)",
            "Arabic (ar)",
            "Russian (ru)",
            "Swahili (sw)",
            "Japanese (ja)",
            "Korean (ko)",
            "Portuguese (pt)",
            "Italian (it)",
            "Dutch (nl)",
            "Hindi (hi)",
            "Turkish (tr)",
            "Thai (th)",
            "Vietnamese (vi)"
        ]

        lang_dropdown = ctk.CTkOptionMenu(settings_frame, variable=self.lang_var, values=languages, width=300)
        lang_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Model info
        self.model_info_text = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=12))
        self.model_info_text.pack(padx=10, pady=5, anchor="w")
        self.update_model_info()  # Initialize with current model

        # Add a trace to update info when model changes
        self.model_var.trace_add("write", lambda *args: self.update_model_info())

        # Process button with progress indicator
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(padx=10, pady=10, fill="x")

        self.process_btn = ctk.CTkButton(
            button_frame,
            text="Transcribe & Translate",
            command=self.start_processing,
            font=ctk.CTkFont(weight="bold"),
            height=40
        )
        self.process_btn.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(button_frame)
        self.progress_bar.pack(pady=(0, 10), fill="x", padx=40)
        self.progress_bar.set(0)

        # Results area
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(padx=10, pady=10, fill="both", expand=True)

        results_label = ctk.CTkLabel(results_frame, text="Results:", anchor="w")
        results_label.pack(padx=10, pady=(10, 5), anchor="w")

        self.results_text = ctk.CTkTextbox(results_frame, wrap="word", height=300)
        self.results_text.pack(padx=10, pady=5, fill="both", expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        status_bar.pack(side="bottom", fill="x", padx=10, pady=5)

    def update_model_info(self):
        model_name = self.model_var.get()
        model_key = self.model_friendly_names.get(model_name, "small")

        # Model descriptions
        model_descriptions = {
            "tiny": "Smallest model, fastest inference, lower accuracy",
            "tiny.en": "Smallest model optimized for English only",
            "base": "Basic model with balanced performance",
            "base.en": "Basic model optimized for English only",
            "small": "Good balance of accuracy and speed",
            "small.en": "Good performance optimized for English only",
            "medium": "High accuracy with moderate speed",
            "medium.en": "High accuracy optimized for English only",
            "large-v1": "High accuracy, first generation large model",
            "large-v2": "Very high accuracy, second generation",
            "large-v3": "State-of-the-art accuracy, third generation",
            "distil-large-v2": "Faster inference with slightly lower accuracy than large-v2",
            "distil-medium.en": "Distilled medium model for faster English processing",
            "distil-small.en": "Distilled small model for faster English processing",
            "distil-large-v3": "Faster inference with slightly lower accuracy than large-v3",
            "large-v3-turbo": "Optimized for faster inference with similar quality to large-v3"
        }

        # Update the info text
        info = model_descriptions.get(model_key, "")
        model_path = self._MODELS.get(model_key, "")

        # Check if it's an English-only model
        is_english = ".en" in model_key
        lang_info = " (English only)" if is_english else " (Multilingual)"

        self.model_info_text.configure(text=f"Selected: {model_name}{lang_info}\n{info}")

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Media Files", "*.wav;*.mp3;*.ogg;*.m4a;*.mp4;*.mkv;*.avi;*.mov")])
        if file_path:
            self.file_path = file_path
            self.entry_file_path.delete(0, "end")
            self.entry_file_path.insert(0, file_path)

    def start_processing(self):
        if self.processing:
            return

        self.file_path = self.entry_file_path.get()

        if not self.file_path:
            messagebox.showerror("Error", "Please select an audio or video file.")
            return

        # Disable the button and show progress
        self.process_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0.05)
        self.status_var.set("Processing file...")
        self.processing = True

        # Start processing in a separate thread
        threading.Thread(target=self.process_media, daemon=True).start()

    def get_model_size(self, model_name):
        # Get the actual model key from the friendly name
        return self.model_friendly_names.get(model_name, "small")

    def process_media(self):
        try:
            # Extract language code from selection
            lang_selection = self.lang_var.get()
            target_lang = None if lang_selection == "None" else lang_selection.split("(")[-1].strip(")")

            # Get model size
            model_key = self.get_model_size(self.model_var.get())

            self.progress_bar.set(0.1)
            self.status_var.set(f"Initializing {self.model_var.get()} model...")

            # Transcribe and translate
            transcription, translation = self.transcribe_and_translate(
                self.file_path,
                model_size=model_key,
                target_lang=target_lang
            )

            # Update UI with results
            self.results_text.delete("0.0", "end")

            if transcription:
                self.results_text.insert("end", "📝 Transcription:\n\n")
                self.results_text.insert("end", f"{transcription}\n\n")

            if translation:
                self.results_text.insert("end", "🌐 Translation:\n\n")
                self.results_text.insert("end", f"{translation}\n")

            self.progress_bar.set(1.0)
            self.status_var.set("Processing complete!")

        except Exception as e:
            self.results_text.delete("0.0", "end")
            self.results_text.insert("end", f"Error: {str(e)}")
            self.status_var.set("Error occurred during processing")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

        finally:
            # Re-enable the button
            self.process_btn.configure(state="normal", text="Transcribe & Translate")
            self.processing = False

    def transcribe_and_translate(self, file_path, model_size="small", target_lang=None):
        device = "cuda" if torch.cuda.is_available() else "cpu"

        self.status_var.set(f"Loading model {model_size} on {device}...")
        self.progress_bar.set(0.2)

        # Get the actual model path
        model_path = self._MODELS.get(model_size, self._MODELS["small"])

        model = WhisperModel(model_size, device=device, download_root=None)

        # Convert video to audio if necessary
        if file_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            self.status_var.set("Converting video to audio...")
            self.progress_bar.set(0.3)

            audio_path = file_path.rsplit(".", 1)[0] + ".wav"
            subprocess.run(["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", audio_path, "-y"], check=True)
        else:
            audio_path = file_path

        self.status_var.set("Transcribing audio...")
        self.progress_bar.set(0.4)

        # Determine if we should use English-only mode
        is_english_model = ".en" in model_size
        language = "en" if is_english_model else None

        segments, info = model.transcribe(audio_path, language=language)

        # Update status with detected language
        detected_lang = info.language
        self.status_var.set(f"Detected language: {detected_lang}")
        self.progress_bar.set(0.7)

        full_transcription = "".join(segment.text + " " for segment in segments).strip()

        translated_text = None
        if target_lang and target_lang != detected_lang:
            self.status_var.set(f"Translating to {target_lang}...")
            self.progress_bar.set(0.8)

            translated_text = GoogleTranslator(source="auto", target=target_lang).translate(full_transcription)

        self.progress_bar.set(0.9)
        return full_transcription, translated_text


def main():
    # Check if required libraries are installed
    try:
        import customtkinter
    except ImportError:
        # If not installed, show message and try to install
        if messagebox.askyesno(
                "Missing Library",
                "CustomTkinter is required but not installed. Would you like to install it now?"
        ):
            subprocess.run(["pip", "install", "customtkinter"])
            messagebox.showinfo("Installation", "Please restart the application.")
            return

    app = GumzoAIApp()
    app.mainloop()


if __name__ == "__main__":
    main()