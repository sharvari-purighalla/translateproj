# frontend_mic.py
import os
import uuid
import streamlit as st
from audiorecorder import audiorecorder  # streamlit-audiorecorder
from pydub import AudioSegment            # needs ffmpeg on system
import tempfile

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from transcribe import transcribe_wav_file
from translate import to_translate_code, translate_text

# ===== App settings =====
st.set_page_config(page_title="🎙️ Live Translate (Mic)", page_icon="🎧", layout="centered")

# Keep consistent with your backend
REGION = os.getenv("AWS_REGION", "us-east-2")
BUCKET = "sharvaristranscribebucket"
INPUT_PREFIX = "audio/"
OUTPUT_PREFIX = "transcripts/"
LANGUAGE_OPTIONS = ["en-US", "es-ES", "fr-FR", "de-DE", "hi-IN", "te-IN"]

st.title("🎙️ Live Translate")
st.caption("Click to record in the browser → we’ll Transcribe on AWS → Translate the text.")

with st.sidebar:
    st.header("⚙️ Settings")
    region = st.selectbox("AWS Region", [REGION, "us-east-1", "us-east-2", "eu-west-1", "ap-south-1"], index=0)
    target_lang = st.selectbox("Target language", ["en", "es", "fr", "de", "it", "ja", "zh", "hi", "te"], index=1)
    st.caption("Uses your existing AWS credentials (env or ~/.aws/credentials).")
    if st.button("Clear output"):
        st.session_state.pop("last_result", None)
        st.experimental_rerun()

st.write("Click to start, click again to stop:")

# This renders a big mic button; returns a pydub.AudioSegment when stopped
audio = audiorecorder("🎙️ Click to record", "🛑 Click to stop")

if len(audio) > 0:
    # audio is pydub.AudioSegment (usually ~44.1kHz stereo)
    st.success("Recording captured!")
    st.audio(audio.export(format="wav").read(), format="audio/wav")

    # Save to a temporary WAV path (16-bit PCM)
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = os.path.join(tmpdir, f"{uuid.uuid4().hex}.wav")
        audio.export(wav_path, format="wav")  # pydub will write a PCM WAV

        try:
            # 1) Transcribe
            text, detected_lang, audio_key, transcript_key = transcribe_wav_file(
                region=region,
                bucket=BUCKET,
                input_prefix=INPUT_PREFIX,
                output_prefix=OUTPUT_PREFIX,
                local_wav_path=wav_path,
                language_options=LANGUAGE_OPTIONS,
                force_language_code=None,  # set to "en-US" to disable auto-detect
            )

            # 2) Translate
            src_for_translate = to_translate_code(detected_lang)
            translated = translate_text(region, text, src_for_translate, target_lang)

            st.session_state["last_result"] = {
                "detected_lang": detected_lang,
                "raw_text": text,
                "translated": translated,
                "target": target_lang,
                "audio_key": audio_key,
                "transcript_key": transcript_key,
            }

        except (BotoCoreError, ClientError) as e:
            st.error(f"AWS error: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# Show result, if any
res = st.session_state.get("last_result")
if res:
    st.subheader("Result")
    st.markdown(f"**Detected language:** `{res['detected_lang']}`  →  **Target:** `{res['target']}`")
    with st.expander("Original transcript"):
        st.write(res["raw_text"] or "_(empty)_")
    with st.expander("Translation"):
        st.write(res["translated"] or "_(empty)_")
    st.caption(f"S3 audio: s3://{BUCKET}/{res['audio_key']}  •  transcript: s3://{BUCKET}/{res['transcript_key']}")
