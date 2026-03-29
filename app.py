import streamlit as st
from extensions.pocketbase import is_authenticated, logout_user, restore_session
from extensions.pocketbase.pocketbase_browser_session import (
    browser_auth_clear_pending,
    flush_browser_auth_clear,
    sync_browser_auth,
)

# Initialize authentication session
if browser_auth_clear_pending():
    flush_browser_auth_clear()
    st.session_state.pop("pb_auth", None)
    st.session_state.pop("user", None)
else:
    restore_session()
    sync_browser_auth(st.session_state.get("pb_auth"))

# Define the pages
pages: dict[str, list[st.Page]] = {}

pages["RAG-LLM"] = [st.Page("pages/ragllm.py", title="RAG-LLM")]

if not is_authenticated():
    pages["User"] = [
        st.Page("pages/authentication/login.py", title="Login"),
    ]

if is_authenticated():
    pages["Logs"] = [st.Page("pages/log/loggerview.py", title="Logs")]
    pages["Documentmanager"] = [
        st.Page("pages/management/documents.py", title="Document Manager"),
        st.Page("pages/views/pdf_view.py", title="PDF View"),
    ]

page_navigation = st.navigation(pages, position="top")
page_navigation.run()
