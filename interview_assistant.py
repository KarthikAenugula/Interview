"""
🎤 Interview Auto Assistant (Resume-Aware Version)
-------------------------------------------------
✅ Upload a resume first, then ask interview questions by text or quick-listen shortcut.
✅ Sends the provided prompt plus resume content to ChatGPT for contextual answers.
✅ Supports microphone capture locally; falls back to text entry in cloud environments.

Built with Streamlit + OpenAI + gTTS
"""

import importlib.util
import os
import platform
import tempfile
from textwrap import dedent

import streamlit as st

# ------------------ DEPENDENCY LOAD ------------------
openai = None
sr = None
gTTS = None
PdfReader = None

if importlib.util.find_spec("openai"):
    import openai  # type: ignore
if importlib.util.find_spec("speech_recognition"):
    import speech_recognition as sr  # type: ignore
if importlib.util.find_spec("gtts"):
    from gtts import gTTS  # type: ignore
if importlib.util.find_spec("pypdf"):
    from pypdf import PdfReader  # type: ignore

if not all([openai, sr, gTTS, PdfReader]):
    st.warning("⚠️ Some audio or PDF libraries couldn't load (expected in cloud mode).")


# ------------------ PAGE SETUP ------------------
st.set_page_config(page_title="🎧 Resume Aware Interview Assistant", layout="centered")
st.title("🎧 Resume Aware Interview Assistant")
st.markdown(
    "Upload your resume first. Then ask questions or use the quick-listen shortcut to feed audio."
)


# ------------------ CONFIGURATION ------------------
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")

SYSTEM_PROMPT = dedent(
    """
    Consider this is your profile and act as candidate you were in the interview and I will be the
    interviewer asking you the questions. Send me the answers only when I ask the prompt and
    coding answers should be different if someone ask the same question again. If its coding send
    me with brief explanation and time and space complexity and no intros in the starting of the
    answers.
    """
)


# ------------------ CORE FUNCTIONS ------------------
def extract_resume_text(uploaded_file):
    """Extract text from uploaded resume (supports PDF and text)."""
    try:
        if uploaded_file.type == "application/pdf":
            if not PdfReader:
                st.error("PDF reading is unavailable in this environment.")
                return None
            reader = PdfReader(uploaded_file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        content = uploaded_file.read()
        return content.decode("utf-8", errors="ignore")
    except Exception as exc:
        st.error(f"Could not read resume: {exc}")
        return None


def get_chatgpt_answer(question, resume_text):
    """Send question + resume context to ChatGPT and return the answer."""
    if not resume_text:
        st.warning("Please upload a resume first so responses are contextual.")
        return None
    if not openai:
        st.error("OpenAI package is unavailable. Set it up to generate answers.")
        return None

    full_prompt = dedent(
        f"""
        {SYSTEM_PROMPT}

        Resume summary:
        {resume_text}

        Interviewer question: {question}
        """
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": full_prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        st.error(f"OpenAI API Error: {exc}")
        return None


def speak_text(text):
    """Speak out the text using gTTS (local use only)."""
    if not gTTS:
        st.warning("Speech playback is unavailable in this environment.")
        return
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            system = platform.system().lower()
            if system.startswith("win"):
                os.system(f"start {fp.name}")  # Windows
            elif system == "darwin":
                os.system(f"afplay {fp.name}")  # macOS
            else:
                os.system(f"xdg-open {fp.name}")  # Linux/other
    except Exception as exc:
        st.warning(f"Speech playback not available: {exc}")


def listen_and_transcribe():
    """Listen from mic and convert to text (local only)."""
    if not sr:
        st.error("Speech recognition is unavailable in this environment.")
        return None
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎙️ Listening via quick shortcut... Speak your question.")
            audio = recognizer.listen(source, phrase_time_limit=15)
            st.info("🧠 Converting speech to text...")
            return recognizer.recognize_google(audio)
    except Exception as exc:
        st.error(f"Speech recognition failed: {exc}")
        return None


# ------------------ MODE DETECTION ------------------
IS_CLOUD = (
    os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud"
    or sr is None
    or not hasattr(sr, "Microphone")
)


# ------------------ MAIN UI ------------------
st.subheader("1) Upload resume")
uploaded_resume = st.file_uploader("Upload PDF or text resume", type=["pdf", "txt"])

if uploaded_resume:
    resume_text = extract_resume_text(uploaded_resume)
    st.session_state["resume_text"] = resume_text
    if resume_text:
        st.success("Resume loaded. The assistant will use it for every answer.")
else:
    resume_text = st.session_state.get("resume_text")

st.markdown("---")
st.subheader("2) Ask your interview question")
status_placeholder = st.empty()
question_placeholder = st.empty()
answer_placeholder = st.empty()

if IS_CLOUD:
    st.warning("☁️ Running in Streamlit Cloud — microphone shortcut not available here.")
    user_input = st.text_input("💬 Type your question below:")
    if st.button("Generate Answer") and user_input.strip():
        with st.spinner("Generating answer..."):
            answer = get_chatgpt_answer(user_input, resume_text)
            if answer:
                answer_placeholder.success(answer)
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.text_input("💬 Type your question (or use the quick-listen shortcut)")
    with col2:
        listen_clicked = st.button("🎯 Quick Listen")

    if user_input.strip() and st.button("Generate Answer", key="text_generate"):
        with st.spinner("Generating answer..."):
            answer = get_chatgpt_answer(user_input, resume_text)
            if answer:
                question_placeholder.markdown(f"**📝 Prompt:** {user_input}")
                answer_placeholder.success(f"💬 **AI Answer:** {answer}")
                speak_text(answer)
                status_placeholder.success("✅ Answer displayed and spoken aloud.")

    if listen_clicked:
        question = listen_and_transcribe()
        if question:
            question_placeholder.markdown(f"**🎧 Shortcut captured:** {question}")
            answer_placeholder.markdown("_Generating answer..._")
            answer = get_chatgpt_answer(question, resume_text)
            if answer:
                answer_placeholder.success(f"💬 **AI Answer:** {answer}")
                speak_text(answer)
                status_placeholder.success("✅ Answer displayed and spoken aloud.")
        else:
            status_placeholder.error("❌ Could not understand speech. Try again.")

st.markdown("---")
st.caption("Built with ❤️ using Streamlit, OpenAI GPT-4o, and resume-aware context")
