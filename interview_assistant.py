"""
🎤 Interview Auto Assistant (Universal Version)
------------------------------------------------
✅ Works locally with microphone (speech → ChatGPT → spoken answer)
✅ Works on Streamlit Cloud with text input (no mic dependency)

Built with Streamlit + OpenAI + gTTS
"""

import streamlit as st
import tempfile
import os

# ------------------ DEPENDENCY LOAD ------------------
try:
    import openai
    import speech_recognition as sr
    from gtts import gTTS
except Exception as e:
    st.warning("⚠️ Some audio libraries couldn't load (expected in cloud mode).")

# ------------------ PAGE SETUP ------------------
st.set_page_config(page_title="🎧 Interview Auto Assistant", layout="centered")
st.title("🎧 Interview Auto Assistant")
st.markdown("Speak or type your interview question — the assistant will respond confidently.")

# ------------------ CONFIGURATION ------------------
# Load API key
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")

SYSTEM_PROMPT = """
You are an experienced senior software developer attending a technical interview.
Answer confidently, clearly, and naturally — avoid robotic tone and sound human.
Keep answers concise (under 120 words) unless detailed explanation is needed.
"""

# ------------------ CORE FUNCTIONS ------------------
def get_chatgpt_answer(question):
    """Send text question to ChatGPT and return a natural answer."""
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
        st.error(f"OpenAI API Error: {e}")
        return None

def speak_text(text):
    """Speak out the text using gTTS (local use only)."""
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            os.system(f'start {fp.name}')  # Windows
    except Exception as e:
        st.warning(f"Speech playback not available: {e}")

def listen_and_transcribe():
    """Listen from mic and convert to text (local only)."""
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎙 Listening... Speak your question.")
            audio = r.listen(source, phrase_time_limit=15)
            st.info("🧠 Converting speech to text...")
            text = r.recognize_google(audio)
            return text
    except Exception as e:
        st.error(f"Speech recognition failed: {e}")
        return None

# ------------------ MODE DETECTION ------------------
# Check if running on Streamlit Cloud (no mic support)
IS_CLOUD = os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud" or not hasattr(sr, "Microphone")

# ------------------ MAIN UI ------------------
status_placeholder = st.empty()
question_placeholder = st.empty()
answer_placeholder = st.empty()

if IS_CLOUD:
    st.warning("☁️ Running in Streamlit Cloud — microphone not available.")
    user_input = st.text_input("💬 Type your question below:")
    if st.button("Generate Answer") and user_input.strip():
        with st.spinner("Generating answer..."):
            answer = get_chatgpt_answer(user_input)
            if answer:
                st.success(answer)
else:
    if st.button("🎤 Start Listening"):
        question = listen_and_transcribe()
        if question:
            question_placeholder.markdown(f"**🗣 You said:** {question}")
            answer_placeholder.markdown("_Generating answer..._")
            answer = get_chatgpt_answer(question)
            if answer:
                answer_placeholder.success(f"💬 **AI Answer:** {answer}")
                speak_text(answer)
                status_placeholder.success("✅ Answer displayed and spoken aloud.")
        else:
            status_placeholder.error("❌ Could not understand speech. Try again.")

st.markdown("---")
st.caption("Built with ❤️ using Streamlit and OpenAI GPT-4o")
