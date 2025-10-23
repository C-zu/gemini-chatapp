import streamlit as st
from dotenv import load_dotenv
from components.sidebar import render_sidebar
from core_chat import render_core_chat
from image_chat import render_image_chat
from csv_chat import render_csv_chat
from utils.database_setup import setup_database_tables

# === Setup ===
load_dotenv()
st.set_page_config(page_title="Gemini Chat", layout="wide")
setup_database_tables()

# === Session state init ===
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {}
if "current_session" not in st.session_state:
    st.session_state.current_session = None
if "show_new_chat" not in st.session_state:
    st.session_state.show_new_chat = True
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "core"
if "session_data" not in st.session_state:
    st.session_state.session_data = {}

# === Sidebar ===
render_sidebar()

# === Main UI ===
mode_titles = {
    "core": "💬 Core Chat",
    "image": "🖼️ Image Chat", 
    "csv": "📊 CSV Chat"
}

mode_descriptions = {
    "core": "Multi-turn text conversations with full history",
    "image": "Upload and ask questions about images", 
    "csv": "Analyze and query CSV data files"
}

if st.session_state.current_session is not None or st.session_state.show_new_chat:
    st.subheader(mode_titles[st.session_state.current_mode])
    st.caption(mode_descriptions[st.session_state.current_mode])

    if st.session_state.current_mode == "core":
        render_core_chat()
    elif st.session_state.current_mode == "image":
        render_image_chat()
    elif st.session_state.current_mode == "csv":
        render_csv_chat()
else:
    st.info("👈 Select a chat from the sidebar or create a new one to get started!")

st.markdown("---")
st.caption("💡 **Tip**: Switch modes in the sidebar to access different chat features")