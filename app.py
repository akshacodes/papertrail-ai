import streamlit as st
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
import os
import time
import google.generativeai as genai

# ————— CONFIG —————
st.set_page_config(page_title="PaperTrail AI", layout="wide")

# Load Gemini key
if "google" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["google"]["api_key"]
else:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Initialize sessions
if "sessions" not in st.session_state:
    st.session_state.sessions = {}
    st.session_state.current = None

# Helper to generate next chat name
def next_chat_name():
    i = 1
    while f"Chat {i}" in st.session_state.sessions:
        i += 1
    return f"Chat {i}"

# On first load, create the first session
if st.session_state.current is None:
    first = next_chat_name()
    st.session_state.sessions[first] = {"combined_text": "", "chat_history": []}
    st.session_state.current = first

# ————— SIDEBAR —————
with st.sidebar:
    st.header("📁 PaperTrailAI")

    # Rename current chat
    new_name = st.text_input(
        "Chat name",
        value=st.session_state.current,
        key="rename_input"
    )
    if new_name and new_name != st.session_state.current:
        if new_name in st.session_state.sessions:
            st.warning("That name already exists.")
        else:
            data = st.session_state.sessions.pop(st.session_state.current)
            st.session_state.sessions[new_name] = data
            st.session_state.current = new_name

    st.markdown("---")

    # Selector
    names = list(st.session_state.sessions.keys())
    sel = st.selectbox("Switch to chat:", names, index=names.index(st.session_state.current))
    st.session_state.current = sel

    # Delete button
    if st.button("🗑️ Delete Chat"):
        # remove the session
        st.session_state.sessions.pop(st.session_state.current)
        # pick a new current or create one
        if st.session_state.sessions:
            st.session_state.current = next(iter(st.session_state.sessions))
        else:
            fresh = next_chat_name()
            st.session_state.sessions[fresh] = {"combined_text": "", "chat_history": []}
            st.session_state.current = fresh
        st.experimental_rerun()  # rerun so UI resets to new session

    st.markdown("---")

    # New chat
    if st.button("➕ New Document / Chat"):
        name = next_chat_name()
        st.session_state.sessions[name] = {"combined_text": "", "chat_history": []}
        st.session_state.current = name

    st.markdown("---")
    st.header("📤 Upload & Extract")
    files = st.file_uploader(
        "PDFs & Images",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="uploader"
    )
    if st.button("📥 Submit", key="submit_extract"):
        # clear chat history for this session
        st.session_state.sessions[st.session_state.current]["chat_history"] = []
        texts = []
        for f in files or []:
            try:
                if f.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=f.read(), filetype="pdf")
                    texts.append("".join(p.get_text() for p in doc))
                else:
                    img = Image.open(f)
                    texts.append(pytesseract.image_to_string(img))
            except Exception as e:
                st.error(f"Error reading {f.name}: {e}")
        combined = "\n".join(texts).strip()
        st.session_state.sessions[st.session_state.current]["combined_text"] = combined
        if combined:
            st.success("✅ Text extracted!")
        else:
            st.warning("⚠️ No text extracted.")

# ————— MAIN CHAT AREA —————
st.title(f"📄 {st.session_state.current}")

session = st.session_state.sessions[st.session_state.current]

# Render past chat
for role, msg in session["chat_history"]:
    with st.chat_message(role):
        st.write(msg)

# Chat input if text exists
if session["combined_text"]:
    if prompt := st.chat_input("💬 Ask a question..."):
        session["chat_history"].append(("user", prompt))
        with st.spinner("🧠 Generating your answer..."):
            full_prompt = (
                f"Use the following content to answer the question.\n\n"
                f"{session['combined_text']}\n\n"
                f"Question:\n{prompt}"
            )
            try:
                model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
                res = model.generate_content(full_prompt)
                answer = res.text
            except Exception as e:
                answer = f"Error calling API: {e}"
        session["chat_history"].append(("assistant", answer))
        with st.chat_message("assistant"):
            st.write(answer)
else:
    st.info("Upload files in the sidebar and click Submit to extract text before chatting.")
