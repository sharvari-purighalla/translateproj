# main.py
"""
CLI loop for a two-person translation chat:
- Person speaks (press 'q' to start/stop)
- Audio is uploaded to S3
- Transcribed with Amazon Transcribe (auto-detect language)
- Translated to the other person's target language
"""

from __future__ import annotations
import uuid

from audio import record_wav_on_q_toggle
from transcribe import transcribe_wav_file
from translate import to_translate_code, translate_text

# --- config ---
# keep your bucket's region and these clients consistent.
REGION = "us-east-1"
BUCKET = "nca-translate-bucket"
INPUT_PREFIX = "audio/"
OUTPUT_PREFIX = "transcripts/"

# Suggest a shortlist for IdentifyLanguage (faster/more accurate than open-ended)
LANGUAGE_OPTIONS = ["en-US", "es-ES", "fr-FR", "de-DE", "hi-IN", "te-IN"]


def one_turn(speaker: str, listener: str, listener_lang: str) -> None:
    """
    Record the speaker, transcribe (auto-detect), translate to the listener's target language,
    and print both original + translated text.
    """
    file_name = f"{uuid.uuid4().hex}.wav"
    wav_path = record_wav_on_q_toggle(file_name)
    if not wav_path:
        print("[warn] Nothing recorded.")
        return

    text, detected_lang, _, _ = transcribe_wav_file(
        region=REGION,
        bucket=BUCKET,
        input_prefix=INPUT_PREFIX,
        output_prefix=OUTPUT_PREFIX,
        local_wav_path=wav_path,
        language_options=LANGUAGE_OPTIONS,
        force_language_code=None,  # set to e.g. "en-US" to disable auto-detect
    )

    if not text.strip():
        print("[tx] Empty transcript.")
        return

    src_lang_for_translate = to_translate_code(detected_lang)
    translation = translate_text(REGION, text, src_lang_for_translate, listener_lang)

    print(f"\n[{speaker}] (detected {detected_lang})")
    print(text)
    print(f"\n[→ {listener} | {listener_lang}]")
    print(translation)
    print("-" * 60)


def main() -> None:
    print("Live Translate Chat — press 'q' to start, 'q' again to stop for each turn.\n")

    # Clarify prompts so each person sets what the OTHER receives
    p1 = input("Person 1 name >> ").strip() or "Person 1"
    p2_target_for_other = input(f"{p1} what language do you want to receive? (e.g., es, fr, hi) >> ").strip() or "es"

    p2 = input("Person 2 name >> ").strip() or "Person 2"
    p1_target_for_other = input(f"({p2} what language do you want to recieve? (e.g., en, fr, hi) >> ").strip() or "en"

    while True:
        print(f"\n🎤 {p1}, your turn.")
        one_turn(p1, p2, p1_target_for_other)

        print(f"\n🎤 {p2}, your turn.")
        one_turn(p2, p1, p2_target_for_other)


if __name__ == "__main__":
    main()
