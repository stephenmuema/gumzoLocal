import requests
import torch
import tkinter as tk
from tkinter import filedialog, messagebox
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
import os
import subprocess
import threading
import customtkinter as ctk
import time
import datetime
import sounddevice as sd
import soundfile as sf

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class GumzoAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Gumzo AI - Speech Transcription & Translation")
        self.geometry("850x650")

        # Variables
        self.file_path = ""
        self.model_var = tk.StringVar(value="Gumzo AI Standard (Small)")
        self.model_language_var = tk.StringVar(value="All Languages")
        self.lang_var = tk.StringVar(value="None")
        self.processing = False
        self.stream_var = tk.BooleanVar(value=True)
        self.segments = []
        self.transcription = ""
        self.translation = ""
        self.cancel_processing = False
        self.streaming_buffer = []
        self.audio_duration = 0

        # New: Input source selection variable ("File" or "Realtime")
        self.input_source_var = tk.StringVar(value="File")

        # Model mappings
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

        # Model friendly names to be shown in the dropdown
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

        # Define ranking (lower numbers = better accuracy)
        self.model_ranking = {
            "Gumzo AI Pro (v3)": 1,
            "Gumzo AI Pro (v2)": 2,
            "Gumzo AI Pro (v1)": 3,
            "Gumzo AI Flash (v3 Flash)": 4,
            "Gumzo AI Pro (Distilled v3)": 5,
            "Gumzo AI Pro (Distilled v2)": 6,
            "Gumzo AI Premium (Medium)": 7,
            "Gumzo AI Premium (English Only)": 7.1,
            "Gumzo AI Standard (Small)": 8,
            "Gumzo AI Standard (English Only)": 8.1,
            "Gumzo AI Lite (Distilled Medium - English)": 9,
            "Gumzo AI Lite (Distilled Small - English)": 10,
            "Gumzo AI Starter (Base)": 11,
            "Gumzo AI Starter (English Only)": 11.1,
            "Gumzo AI Basic (Tiny)": 12,
            "Gumzo AI Basic (English Only)": 12.1,
        }

        # Create UI
        self.create_ui()

    def create_ui(self):
        # Create a scrollable frame
        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.pack(padx=10, pady=10, fill="both", expand=True)

        # Main frame - now inside the scrollable container
        main_frame = ctk.CTkFrame(self.main_container)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Header
        title_label = ctk.CTkLabel(main_frame, text="Gumzo AI Transcription",
                                   font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(0, 10))

        description = ctk.CTkLabel(main_frame,
                                   text="Convert speech to text and translate to different languages",
                                   font=ctk.CTkFont(size=14))
        description.pack(pady=(0, 20))

        # --- Input Source Selection ---
        input_source_frame = ctk.CTkFrame(main_frame)
        input_source_frame.pack(padx=10, pady=10, fill="x")
        input_source_label = ctk.CTkLabel(input_source_frame, text="Input Source:")
        input_source_label.pack(side="left", padx=(10, 5))
        file_radio = ctk.CTkRadioButton(input_source_frame, text="File", variable=self.input_source_var, value="File")
        file_radio.pack(side="left", padx=5)
        mic_radio = ctk.CTkRadioButton(input_source_frame, text="Realtime (Microphone)", variable=self.input_source_var, value="Realtime")
        mic_radio.pack(side="left", padx=5)

        # Trace changes to input_source_var to update file selector visibility
        self.input_source_var.trace_add("write", self.toggle_file_selector)

        # File selection (only used when File is chosen)
        self.file_frame = ctk.CTkFrame(main_frame)
        self.file_frame.pack(padx=10, pady=10, fill="x")
        file_label = ctk.CTkLabel(self.file_frame, text="Audio/Video File:")
        file_label.pack(side="left", padx=(10, 5))
        self.entry_file_path = ctk.CTkEntry(self.file_frame, width=400)
        self.entry_file_path.pack(side="left", padx=5, fill="x", expand=True)
        browse_btn = ctk.CTkButton(self.file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side="left", padx=5)

        # Settings (store as instance variable for ordering)
        self.settings_frame = ctk.CTkFrame(main_frame)
        self.settings_frame.pack(padx=10, pady=10, fill="x")

        # Model selection
        model_frame = ctk.CTkFrame(self.settings_frame)
        model_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        model_label = ctk.CTkLabel(model_frame, text="Model:")
        model_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        # Sort models using our ranking dictionary (best to worst)
        models = sorted(self.model_friendly_names.keys(), key=lambda x: self.model_ranking.get(x, 100))
        model_dropdown = ctk.CTkOptionMenu(model_frame, variable=self.model_var, values=models, width=300)
        model_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Language selection
        lang_frame = ctk.CTkFrame(self.settings_frame)
        lang_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        lang_label = ctk.CTkLabel(lang_frame, text="Translate to:")
        lang_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        lang_dict = GoogleTranslator().get_supported_languages(as_dict=True)
        languages = ["None"] + [f"{name} ({code})" for name, code in sorted(lang_dict.items(), key=lambda x: x[0])]
        lang_dropdown = ctk.CTkOptionMenu(lang_frame, variable=self.lang_var, values=languages, width=150)
        lang_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_frame.grid_columnconfigure(1, weight=1)

        self.model_info_text = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=12))
        self.model_info_text.pack(padx=10, pady=5, anchor="w")
        self.update_model_info()
        self.model_var.trace_add("write", lambda *args: self.update_model_info())

        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(padx=10, pady=5, fill="x")
        self.process_btn = ctk.CTkButton(
            button_frame,
            text="Transcribe & Translate",
            command=self.start_processing,
            font=ctk.CTkFont(weight="bold"),
            height=40,
            width=200
        )
        self.process_btn.pack(side="left", padx=10, pady=10)
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel_processing_task,
            font=ctk.CTkFont(weight="bold"),
            height=40,
            width=100,
            fg_color="#d32f2f",
            hover_color="#b71c1c"
        )
        self.cancel_btn.pack(side="left", padx=10, pady=10)
        self.cancel_btn.configure(state="disabled")

        # Progress
        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_frame.pack(padx=10, pady=5, fill="x")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(pady=5, fill="x", padx=10)
        self.progress_bar.set(0)

        # Results
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(padx=10, pady=5, fill="both", expand=True)
        self.results_tabs = ctk.CTkTabview(results_frame)
        self.results_tabs.pack(padx=5, pady=5, fill="both", expand=True)
        self.transcript_tab = self.results_tabs.add("Transcript")
        self.translation_tab = self.results_tabs.add("Translation")
        self.transcript_text = ctk.CTkTextbox(self.transcript_tab, wrap="word", height=200)
        self.transcript_text.pack(padx=5, pady=5, fill="both", expand=True)
        self.translation_text = ctk.CTkTextbox(self.translation_tab, wrap="word", height=200)
        self.translation_text.pack(padx=5, pady=5, fill="both", expand=True)

        # Export
        export_frame = ctk.CTkFrame(main_frame)
        export_frame.pack(padx=10, pady=5, fill="x")
        export_txt_btn = ctk.CTkButton(
            export_frame,
            text="Export as TXT",
            command=self.export_txt,
            height=30,
            width=120
        )
        export_txt_btn.pack(side="left", padx=10, pady=10)
        export_srt_btn = ctk.CTkButton(
            export_frame,
            text="Export as SRT",
            command=self.export_srt,
            height=30,
            width=120
        )
        export_srt_btn.pack(side="left", padx=10, pady=10)

        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        status_bar.pack(side="bottom", fill="x", padx=10, pady=5)

    def toggle_file_selector(self, *args):
        # Show file selector only if the input source is set to "File"
        if self.input_source_var.get() == "Realtime":
            self.file_frame.pack_forget()
        else:
            # Re-pack before the settings frame so the order stays consistent
            self.file_frame.pack(padx=10, pady=10, fill="x", before=self.settings_frame)

    def update_model_info(self):
        model_name = self.model_var.get()
        model_key = self.model_friendly_names.get(model_name, "small")
        descriptions = {
            "tiny": "Fastest but least accurate (multilingual)",
            "tiny.en": "Fastest English-only model",
            "base": "Balance of speed and accuracy (multilingual)",
            "base.en": "Base English-only model",
            "small": "Recommended for most users (multilingual)",
            "small.en": "Small English-only model",
            "medium": "High accuracy (multilingual)",
            "medium.en": "Medium English-only model",
            "large-v1": "Original large model (v1)",
            "large-v2": "Improved large model (v2)",
            "large-v3": "Latest large model (v3)",
            "distil-large-v2": "Distilled version of large-v2",
            "distil-large-v3": "Distilled version of large-v3",
            "distil-medium.en": "Distilled medium English model",
            "distil-small.en": "Distilled small English model",
            "large-v3-turbo": "Optimized for fast inference"
        }
        lang_info = " (English only)" if ".en" in model_key else " (Multilingual)"
        info = descriptions.get(model_key, "Good balance of speed and accuracy")
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

        # Reset state and UI elements
        self.transcript_text.delete("1.0", "end")
        self.translation_text.delete("1.0", "end")
        self.segments = []
        self.transcription = ""
        self.translation = ""
        self.cancel_processing = False
        self.streaming_buffer = []
        self.progress_bar.set(0.0)

        self.process_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")

        # Determine input source and start appropriate processing
        if self.input_source_var.get() == "File":
            if not self.file_path:
                messagebox.showerror("Error", "Please select an audio or video file.")
                self.process_btn.configure(state="normal")
                self.cancel_btn.configure(state="disabled")
                return
            self.status_var.set("Processing file...")
            self.processing = True
            threading.Thread(target=self.process_media, daemon=True).start()
        else:  # Realtime (Microphone) mode
            self.status_var.set("Starting realtime transcription...")
            self.processing = True
            threading.Thread(target=self.realtime_transcription, daemon=True).start()

    def cancel_processing_task(self):
        if self.processing:
            self.cancel_processing = True
            self.status_var.set("Cancelling...")

    def estimate_total_duration(self, audio_path):
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ], capture_output=True, text=True)
            return float(result.stdout.strip())
        except:
            return 60  # Fallback duration

    def process_media(self):
        try:
            if self.file_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                self.status_var.set("Converting video to audio...")
                audio_path = self.file_path.rsplit(".", 1)[0] + ".wav"
                subprocess.run(
                    ["ffmpeg", "-i", self.file_path, "-q:a", "0", "-map", "a", audio_path, "-y"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                audio_path = self.file_path

            self.audio_duration = self.estimate_total_duration(audio_path)
            model_key = self.model_friendly_names.get(self.model_var.get(), "small")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.status_var.set(f"Loading model on {device}...")
            default = os.path.join(os.path.expanduser("~"), ".cache")
            download_root = os.path.join(os.getenv("XDG_CACHE_HOME", default), "gumzo")
            os.makedirs(download_root, exist_ok=True)
            model = WhisperModel(model_key, device=device, download_root=download_root)

            lang_selection = self.lang_var.get()
            target_lang = None if lang_selection == "None" else lang_selection.split("(")[-1].strip(")")
            is_english_model = ".en" in model_key
            language = "en" if is_english_model else None

            self.status_var.set("Starting transcription...")
            self.progress_bar.set(0.1)
            segment_generator, info = model.transcribe(
                audio_path,
                language=language,
                beam_size=5
            )
            segments = list(segment_generator)
            full_transcription = " ".join([seg.text for seg in segments])
            self.transcript_text.insert("end", full_transcription)
            self.progress_bar.set(0.8)

            translated_text = ""
            if target_lang and full_transcription.strip():
                try:
                    try:
                        requests.get("https://www.google.com", timeout=5)
                    except requests.ConnectionError:
                        self.translation_text.insert("end", "Translation requires internet connection")
                        return

                    supported_langs = GoogleTranslator().get_supported_languages(as_dict=True)
                    if target_lang not in supported_langs.values():
                        self.translation_text.insert("end", f"Unsupported language: {target_lang}")
                        return

                    chunk_size = 4500
                    chunks = [full_transcription[i:i + chunk_size] for i in range(0, len(full_transcription), chunk_size)]
                    total_chunks = len(chunks)
                    translated_chunks = []

                    self.status_var.set(f"Translating 0/{total_chunks} chunks...")
                    self.progress_bar.set(0.8)

                    for i, chunk in enumerate(chunks):
                        if self.cancel_processing:
                            break
                        try:
                            translated = GoogleTranslator(source="auto", target=target_lang).translate(chunk)
                            translated_chunks.append(translated)
                        except Exception as e:
                            translated_chunks.append(f"\n[TRANSLATION ERROR IN CHUNK {i + 1}: {str(e)}]\n")
                        progress = 0.8 + (0.2 * (i + 1) / total_chunks)
                        self.progress_bar.set(progress)
                        self.status_var.set(f"Translating {i + 1}/{total_chunks} chunks...")
                        time.sleep(1.5)
                    translated_text = " ".join(translated_chunks)
                    self.translation_text.insert("end", translated_text)
                except Exception as e:
                    error_msg = f"Translation failed: {str(e)}\nPossible causes:\n- Service timeout\n- Invalid API response\n- Daily quota exceeded"
                    self.translation_text.insert("end", error_msg)

            self.segments = segments
            self.transcription = full_transcription.strip()
            self.translation = translated_text.strip()
            self.progress_bar.set(1.0)
            self.status_var.set("Processing complete!" if not self.cancel_processing else "Processing cancelled")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
        finally:
            self.processing = False
            self.process_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")

    def realtime_transcription(self):
        try:
            sample_rate = 16000
            duration = 5
            model_key = self.model_friendly_names.get(self.model_var.get(), "small")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.status_var.set(f"Loading model on {device} for realtime transcription...")
            default = os.path.join(os.path.expanduser("~"), ".cache")
            download_root = os.path.join(os.getenv("XDG_CACHE_HOME", default), "gumzo")
            os.makedirs(download_root, exist_ok=True)
            model = WhisperModel(model_key, device=device, download_root=download_root)
            self.status_var.set("Realtime transcription started. Speak into your microphone...")
            while not self.cancel_processing:
                self.status_var.set("Recording...")
                recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
                sd.wait()
                temp_audio_path = "temp_realtime.wav"
                sf.write(temp_audio_path, recording, sample_rate)
                self.status_var.set("Transcribing...")
                segment_generator, info = model.transcribe(temp_audio_path, language=None, beam_size=5)
                segments = list(segment_generator)
                if segments:
                    chunk_text = " ".join([seg.text for seg in segments])
                    self.transcript_text.insert("end", chunk_text + "\n")
                    self.transcript_text.see("end")
                    lang_selection = self.lang_var.get()
                    if lang_selection != "None":
                        target_lang = lang_selection.split("(")[-1].strip(")")
                        try:
                            translated = GoogleTranslator(source="auto", target=target_lang).translate(chunk_text)
                            self.translation_text.insert("end", translated + "\n")
                            self.translation_text.see("end")
                        except Exception as e:
                            self.translation_text.insert("end", f"\n[Translation Error: {str(e)}]\n")
                            self.translation_text.see("end")
                time.sleep(0.2)
            self.status_var.set("Realtime transcription stopped.")
        except Exception as e:
            self.status_var.set(f"Error in realtime transcription: {str(e)}")
            messagebox.showerror("Realtime Transcription Error", f"{str(e)}")
        finally:
            self.processing = False
            self.process_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")

    def export_txt(self):
        if not self.transcription:
            messagebox.showinfo("Export", "No transcription available to export.")
            return
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt")],
                initialfile=os.path.basename(self.file_path).rsplit(".", 1)[0] + "_transcript.txt"
            )
            if not file_path:
                return
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.transcription)
                if self.translation:
                    f.write("\n\n--- TRANSLATION ---\n\n")
                    f.write(self.translation)
            messagebox.showinfo("Export", f"Exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def export_srt(self):
        if not self.segments:
            messagebox.showinfo("Export", "No segments available for SRT export.")
            return
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".srt",
                filetypes=[("SRT Files", "*.srt")],
                initialfile=os.path.basename(self.file_path).rsplit(".", 1)[0] + ".srt"
            )
            if not file_path:
                return
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(self.segments, 1):
                    start = self.format_srt_time(seg.start)
                    end = self.format_srt_time(seg.end)
                    f.write(f"{i}\n{start} --> {end}\n{seg.text}\n\n")
            messagebox.showinfo("Export", f"SRT file exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export SRT: {str(e)}")

    def format_srt_time(self, seconds):
        td = datetime.timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def main():
    app = GumzoAIApp()
    app.mainloop()

if __name__ == "__main__":
    main()
