import streamlit as st

from application.app_session import reset_chat_context

def render_new_chat():
    if st.button("🆕 New chat", use_container_width=True):
        start_new_chat()
        st.rerun()

def start_new_chat():
    """Start a fresh conversation without rebuilding the current index."""
    reset_chat_context(st)
