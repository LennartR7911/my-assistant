import streamlit as st
import threading
import time
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.core.config import settings
from src.services.input_handler import start_input_watcher
from src.services.task_enricher import TaskEnricher
from src.services.daily_setup import generate_daily_log
from src.services.project_manager import create_project

# Page Config
st.set_page_config(
    page_title="Life OS Dashboard",
    page_icon="🧠",
    layout="wide"
)

# Background Services Management
if 'services_started' not in st.session_state:
    st.session_state.services_started = False

def start_services():
    if not st.session_state.services_started:
        # 1. Daily Log
        try:
            generate_daily_log()
            st.toast("Daily Log Generated!")
        except Exception as e:
            st.error(f"Daily Log Error: {e}")

        # 2. Input Watcher
        start_input_watcher()
        st.toast("Input Watcher Active")

        # 3. Task Enricher
        enricher = TaskEnricher()
        enricher_thread = threading.Thread(target=enricher.run_loop, daemon=True)
        enricher_thread.start()
        st.toast("Task Enricher Running")

        st.session_state.services_started = True

# Sidebar
st.sidebar.title("Life OS 🧠")
page = st.sidebar.radio("Navigation", ["Home", "Logs", "Projects", "Inbox", "Settings"])

if st.sidebar.button("Start Services"):
    start_services()

if st.session_state.services_started:
    st.sidebar.success("✅ System Online")
else:
    st.sidebar.warning("⚠️ System Offline")

# Pages
if page == "Home":
    st.title("Welcome back, Lennart 👋")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Inbox", len(list((Path(settings.KNOWLEDGE_BASE_PATH) / "Inbox").glob("*"))))
    with col2:
        st.metric("Active Projects", len(list((Path(settings.KNOWLEDGE_BASE_PATH) / "Projects").glob("*"))))
    with col3:
        st.metric("Today's Logs", 1 if (Path(settings.KNOWLEDGE_BASE_PATH) / "Logs" / f"{time.strftime('%Y-%m-%d')}.md").exists() else 0)

    st.subheader("Quick Actions")
    if st.button("Generate Morning Briefing"):
        try:
            from src.services.calendar_agent import CalendarClient
            cal = CalendarClient()
            cal.generate_briefing()
            st.success("Briefing Generated!")
        except Exception as e:
            st.error(f"Failed: {e}")

elif page == "Logs":
    st.title("Daily Logs & Briefings")
    log_dir = Path(settings.KNOWLEDGE_BASE_PATH) / "Logs"
    if log_dir.exists():
        logs = sorted(log_dir.glob("*.md"), reverse=True)
        selected_log = st.selectbox("Select Log", logs, format_func=lambda x: x.name)
        if selected_log:
            with open(selected_log, "r") as f:
                content = f.read()
            st.markdown(content)

            # Simple editor
            new_content = st.text_area("Edit Log", content, height=400)
            if st.button("Save Log"):
                with open(selected_log, "w") as f:
                    f.write(new_content)
                st.success("Saved!")

elif page == "Projects":
    st.title("Project Management")

    with st.expander("Create New Project"):
        with st.form("new_project"):
            name = st.text_input("Project Name")
            client = st.text_input("Client Name")
            submitted = st.form_submit_button("Create")
            if submitted and name and client:
                create_project(name, client)
                st.success(f"Project {name} created!")

    # List Projects
    projects_dir = Path(settings.KNOWLEDGE_BASE_PATH) / "Projects"
    if projects_dir.exists():
        for client_dir in projects_dir.iterdir():
            if client_dir.is_dir():
                st.subheader(f"Client: {client_dir.name}")
                for proj_dir in client_dir.iterdir():
                    st.text(f"📁 {proj_dir.name}")

elif page == "Inbox":
    st.title("Inbox Processing")
    uploaded_file = st.file_uploader("Drop file to Inbox", type=['mp3', 'txt', 'pdf', 'docx', 'png', 'jpg'])
    if uploaded_file:
        inbox_path = Path(settings.KNOWLEDGE_BASE_PATH) / "Inbox" / uploaded_file.name
        with open(inbox_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Saved {uploaded_file.name} to Inbox. Watcher will process it shortly.")

elif page == "Settings":
    st.title("Configuration")
    st.json(settings.model_dump())
