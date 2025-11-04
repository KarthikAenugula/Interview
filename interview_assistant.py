"""
🎤 Interview Auto Assistant
---------------------------
This app listens to live interview questions through your microphone,
transcribes them to text, sends them to ChatGPT for a confident answer,
and optionally speaks the answer aloud.

Built with Streamlit + OpenAI + gTTS.
"""

import streamlit as st
import openai
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os

# ------------------ CONFIGURATION ------------------
st.set_page_config(page_title="🎧 Interview Auto Assistant", layout="centered")

# Load API Key from Streamlit Secrets (recommended for deployment)
# If running locally, you can also replace with: openai.api_key = "sk-xxxx"
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai.api_key = "YOUR_API_KEY_HERE"  # Replace with your key if testing locally

SYSTEM_PROMPT = """
You are an experienced senior software developer attending a technical interview.
Answer confidently, clearly, and naturally — avoid robotic tone and sound human.
Keep answers concise (under 120 words) unless explanation is needed.
"""

# ------------------ STREAMLIT UI ------------------
st.title("🎧 Interview Auto Assistant")
st.markdown("Speak the interviewer’s question, and the AI will respond automatically.")

status_placeholder = st.empty()
question_placeholder = st.empty()
answer_placeholder = st.empty()

# ------------------ FUNCTION DEFINITIONS ------------------
def listen_and_transcribe():
    """Capture audio from microphone and convert to text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        status_placeholder.info("🎙 Listening... Speak now.")
        audio = r.listen(source, phrase_time_limit=15)
        status_placeholder.info("🧠 Converting speech to text...")
        try:
            text = r.recognize_google(audio)
            return text
        except Exception as e:
            st.error(f"Speech recognition error: {e}")
            return None

def get_chatgpt_answer(question):
    """Send transcribed text to ChatGPT and get response."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"ChatGPT API error: {e}")
        return "Error generating response."

def speak_text(text):
    """Convert text to speech using gTTS and play it."""
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            os.system(f'start {fp.name}')  # Works on Windows
    except Exception as e:
        st.error(f"Speech playback error: {e}")

# ------------------ MAIN LOGIC ------------------
if st.button("🎤 Start Listening"):
    question = listen_and_transcribe()

    if question:
        question_placeholder.markdown(f"**🗣 You said:** {question}")
        answer_placeholder.markdown("_Generating answer..._")
        answer = get_chatgpt_answer(question)
        answer_placeholder.success(f"💬 **AI Answer:** {answer}")
        speak_text(answer)
        status_placeholder.success("✅ Answer displayed and spoken aloud.")
    else:
        status_placeholder.error("❌ Could not understand speech. Try again.")

st.markdown("---")
st.caption("Built with ❤️ using Streamlit and OpenAI GPT-4o")
