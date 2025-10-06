# app.py
import os
import textwrap
import streamlit as st
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# =========================
# Config & helpers
# =========================
st.set_page_config(page_title="🌐 AWS Translate Chatbot", page_icon="💬", layout="centered")

DEFAULT_REGION = os.getenv("AWS_REGION", "us-east-2")
LANGS = ["en", "es", "fr", "de", "it", "ja", "zh", "hi", "te"]

# Translate hard limit is ~5,000 bytes/characters; keep some margin
MAX_CHARS = 4500

@st.cache_resource(show_spinner=False)
def get_translate_client(region: str):
    return boto3.client("translate", region_name=region)

def chunks(s: str, n: int):
    """Yield successive n-char chunks from s."""
    for i in range(0, len(s), n):
        yield s[i:i+n]

def translate_text(client, text: str, source_code: str, target_code: str) -> tuple[str, str | None]:
    """
    Returns (translated_text, detected_lang_if_auto)
    If source_code == 'auto', AWS returns DetectedLanguageCode in the response.
    """
    pieces = list(chunks(text, MAX_CHARS))
    out = []
    detected = None
    for p in pieces:
        resp = client.translate_text(
            Text=p,
            SourceLanguageCode="auto" if source_code == "auto" else source_code,
            TargetLanguageCode=target_code
        )
        out.append(resp["TranslatedText"])
        if source_code == "auto":
            # Save the last detected code (they should be consistent)
            detected = resp.get("SourceLanguageCode") or resp.get("DetectedLanguageCode")
    return "".join(out), detected

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.header("⚙️ Settings")
    region = st.selectbox("AWS Region", [DEFAULT_REGION, "us-east-1", "us-east-2", "eu-west-1", "ap-south-1"], index=0)
    auto_detect = st.toggle("Auto-detect input language", value=True)
    source_lang = "auto" if auto_detect else st.selectbox("Source Language", ["en", "es", "fr", "de", "it", "ja", "zh", "hi", "te"], index=0)
    target_lang = st.selectbox("Target Language", ["es", "en", "fr", "de", "it", "ja", "zh", "hi", "te"], index=1)
    st.caption("Tip: set AWS creds via env vars or ~/.aws/credentials.")
    if st.button("Clear chat 🧹"):
        st.session_state.pop("messages", None)
        st.experimental_rerun()

# =========================
# Header & state
# =========================
st.title("💬 AWS Translate Chatbot")
st.write("Type a message and I’ll translate it instantly.")

if "messages" not in st.session_state:
    st.session_state["messages"] = []  # list[dict(role, content, meta?)]

client = get_translate_client(region)

# =========================
# Chat input
# =========================
user_input = st.chat_input("Type your message…")
if user_input:
    try:
        translated, detected = translate_text(client, user_input, source_lang, target_lang)

        # Store both user and assistant messages
        st.session_state["messages"].append({
            "role": "user",
            "content": user_input,
            "meta": {"src": source_lang}
        })
        st.session_state["messages"].append({
            "role": "assistant",
            "content": translated,
            "meta": {"detected": detected, "tgt": target_lang}
        })

    except (BotoCoreError, ClientError) as e:
        st.error(f"Translation error: {e}")

# =========================
# Render chat history
# =========================
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
            if msg.get("meta", {}).get("src") and msg["meta"]["src"] != "auto":
                st.caption(f"Source: {msg['meta']['src']}")
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])
            meta = msg.get("meta", {})
            if meta.get("detected"):
                st.caption(f"Detected source: {meta['detected']}  →  Target: {meta.get('tgt', '')}")
            elif meta.get("tgt"):
                st.caption(f"Target: {meta['tgt']}")
