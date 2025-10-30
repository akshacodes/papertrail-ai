import streamlit as st
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
import os
import time
import google.generativeai as genai

# ————— CONFIG —————
st.set_page_config(page_title="PaperTrail AI", layout="wide")

# Inject custom CSS for chat bubbles and sidebar
st.markdown("""
<style>
    /* Target the chat message containers */
    [data-testid="chat-message-container-user"] [data-testid="stMarkdownContainer"] {
        background-color: #2b313e; /* Darker blue for user */
        border-radius: 8px;
        padding: 12px;
        color: white;
    }

    [data-testid="chat-message-container-assistant"] [data-testid="stMarkdownContainer"] {
        background-color: #1e1e2f; /* Dark purple for assistant */
        border: 1px solid #4a4a6a;
        border-radius: 8px;
        padding: 12px;
        color: #f0f0f0;
    }

    /* Improve sidebar aesthetics */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e; /* Darker sidebar background */
    }
</style>
""", unsafe_allow_html=True)


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
    
    with st.expander("🗂️ Chat Management", expanded=True):
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
                st.experimental_rerun() # Rerun to reflect name change immediately

        # Selector
        names = list(st.session_state.sessions.keys())
        sel_idx = names.index(st.session_state.current) if st.session_state.current in names else 0
        sel = st.selectbox("Switch to chat:", names, index=sel_idx)
        if sel != st.session_state.current:
            st.session_state.current = sel
            st.experimental_rerun() # Rerun to switch session

        # Delete button
        if st.button("🗑️ Delete Chat"):
            st.session_state.sessions.pop(st.session_state.current)
            # pick a new current or create one
            if st.session_state.sessions:
                st.session_state.current = next(iter(st.session_state.sessions))
            else:
                fresh = next_chat_name()
                st.session_state.sessions[fresh] = {"combined_text": "", "chat_history": []}
                st.session_state.current = fresh
            st.experimental_rerun()  # rerun so UI resets to new session

        # New chat
        if st.button("➕ New Document / Chat"):
            name = next_chat_name()
            st.session_state.sessions[name] = {"combined_text": "", "chat_history": []}
            st.session_state.current = name
            st.experimental_rerun() # Rerun to show new chat

    with st.expander("📤 Upload & Extract", expanded=True):
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
            with st.spinner("Extracting text from files..."):
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
                st.success("✅ Text extracted! You can now chat below.")
            else:
                st.warning("⚠️ No text was extracted from the files.")
            st.experimental_rerun() # Rerun to show chat input

# ————— MAIN CHAT AREA —————
st.title(f"📄 {st.session_state.current}")

# Ensure session exists (can happen on fast reruns)
if st.session_state.current not in st.session_state.sessions:
    # This is a fallback, should rarely be hit
    first = next_chat_name()
    st.session_state.sessions[first] = {"combined_text": "", "chat_history": []}
    st.session_state.current = first

session = st.session_state.sessions[st.session_state.current]

# Render past chat
for role, msg in session["chat_history"]:
    with st.chat_message(role):
        st.write(msg) # Using st.write to handle markdown/plain text

# Chat input if text exists
if session["combined_text"]:
    if prompt := st.chat_input("💬 Ask a question about your documents..."):
        session["chat_history"].append(("user", prompt))
        # Display user message immediately
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("🧠 Generating your answer..."):
                full_prompt = (
                    f"Use the following content to answer the question.\n\n"
                    f"--- CONTENT START ---\n"
                    f"{session['combined_text']}\n"
                    f"--- CONTENT END ---\n\n"
                    f"Question:\n{prompt}"
                )
                try:
                    # --- THIS IS THE UPDATED LINE ---
                    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
                    # ------------------------------
                    
                    res = model.generate_content(full_prompt)
                    if res.parts:
                        answer = res.text
                    else:
                        answer = "Sorry, I couldn't generate a response. The model may have blocked the content."
                except Exception as e:
                    answer = f"Error calling API: {e}"
            
            st.write(answer)
            session["chat_history"].append(("assistant", answer))
else:
    # --- Improved "Empty State" Welcome Screen ---
    st.markdown("---")
    col1, col2 = st.columns([1, 3]) # 1:3 ratio for icon and text
    
    with col1:
        # A large emoji as a placeholder logo
        st.markdown("<h1 style='text-align: center; font-size: 5rem; margin-top: 20px;'>📑</h1>", unsafe_allow_html=True)
    
    with col2:
        st.subheader("Welcome to PaperTrail AI!")
        st.markdown("""
        This app helps you chat with your documents.
        
        **Here's how to get started:**
        
        1.  **Look left!** 👈 Use the sidebar to manage your chats.
        2.  Click **"➕ New Document / Chat"** to start a new session.
        3.  In the **"📤 Upload & Extract"** section, upload your PDFs or images.
        4.  Click the **"📥 Submit"** button to process them.
        
        Once your files are processed, the chat box will appear here!
        """)
    
    st.info("Upload files in the sidebar and click Submit to extract text before chatting.", icon="☝️")