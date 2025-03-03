import argparse
import torch
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator


def transcribe_and_translate(audio_path, model_size="medium", target_lang=None):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = WhisperModel(model_size, device=device, compute_type="float16")

    segments, info = model.transcribe(audio_path)
    print(f"Detected language: {info.language}")

    full_transcription = ""
    for segment in segments:
        full_transcription += segment.text + " "

    full_transcription = full_transcription.strip()

    translated_text = None
    if target_lang:
        translated_text = GoogleTranslator(source="auto", target=target_lang).translate(full_transcription)

    return full_transcription, translated_text

