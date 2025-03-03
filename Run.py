import argparse

from main import transcribe_and_translate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe and optionally translate audio using Faster Whisper.")
    parser.add_argument("audio_path", type=str, help="Path to the audio file.")
    parser.add_argument("--model_size", type=str, default="medium",
                        help="Size of the Faster Whisper model (tiny, base, small, medium, large-v2, etc.)")
    parser.add_argument("--target_lang", type=str, default=None, help="Target language for translation (optional).")

    args = parser.parse_args()

    transcription, translation = transcribe_and_translate(args.audio_path, args.model_size, args.target_lang)

    print("Transcription:")
    print(transcription)

    if translation:
        print("\nTranslation:")
        print(translation)
