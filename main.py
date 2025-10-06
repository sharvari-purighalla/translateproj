# main.py
import uuid
from audio import record_wav_on_q_toggle
from transcribe import transcribe_wav_file
from translate import to_translate_code, translate_text

REGION = "us-east-2"
BUCKET = "sharvaristranscribebucket"
INPUT_PREFIX = "audio/"
OUTPUT_PREFIX = "transcripts/"
LANGUAGE_OPTIONS = ["en-US", "es-ES", "fr-FR", "de-DE", "hi-IN", "te-IN"]

def one_turn(speaker, listener, listener_lang):
    """Record, transcribe, and translate speaker’s audio."""
    file_name = f"{uuid.uuid4().hex}.wav"
    wav = record_wav_on_q_toggle(file_name)
    if not wav:
        print("[warn] Nothing recorded.")
        return

    text, detected_lang, _, _ = transcribe_wav_file(
        REGION, BUCKET, INPUT_PREFIX, OUTPUT_PREFIX,
        wav, LANGUAGE_OPTIONS
    )

    if not text.strip():
        print("[tx] Empty transcript.")
        return

    src_lang = to_translate_code(detected_lang)
    translation = translate_text(REGION, text, src_lang, listener_lang)

    print(f"\n[{speaker}] Detected {detected_lang}: {text}")
    print(f"[→ {listener} ({listener_lang})] {translation}\n")

def main():
    print("🎙️ Live Translate Chat — press 'q' to start, 'q' again to stop.\n")
    p1 = input("Person 1 name >> ").strip() or "Person 1"
    p1_target_lang = input("Language for Person 2 to receive (e.g., es, fr, hi) >> ").strip() or "es"

    p2 = input("Person 2 name >> ").strip() or "Person 2"
    p2_target_lang = input("Language for Person 1 to receive (e.g., en, fr, hi) >> ").strip() or "en"

    while True:
        print(f"🎤 {p1}, your turn.")
        one_turn(p1, p2, p1_target_lang)

        print(f"🎤 {p2}, your turn.")
        one_turn(p2, p1, p2_target_lang)

if __name__ == "__main__":
    main()
