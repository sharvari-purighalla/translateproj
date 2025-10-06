import streamlit as st
import boto3

# --- AWS SETTINGS ---
REGION = "us-east-2"  # change to your region
translate_client = boto3.client("translate", region_name=REGION)

# --- Streamlit UI ---
st.set_page_config(page_title="🌐 Translation Chatbot", page_icon="💬")

st.title("💬 AWS Translate Chatbot")
st.write("Type a message and get it translated into another language in real time!")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Language selection
col1, col2 = st.columns(2)
with col1:
    in_lang = st.selectbox("Input Language", ["auto", "en", "es", "fr", "de", "it", "ja", "zh"])
with col2:
    out_lang = st.selectbox("Target Language", ["es", "en", "fr", "de", "it", "ja", "zh"], index=0)

# Chat input box
user_input = st.chat_input("Type your message...")

if user_input:
    # Translate the text
    response = translate_client.translate_text(
        Text=user_input,
        SourceLanguageCode=in_lang if in_lang != "auto" else "auto",
        TargetLanguageCode=out_lang
    )
    translated_text = response["TranslatedText"]

    # Save user + bot messages
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.session_state["messages"].append({"role": "bot", "content": translated_text})

# Display chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])
