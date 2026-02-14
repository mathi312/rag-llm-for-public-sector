import streamlit as st
from extensions.pocketbase import is_authenticated, logout_user, restore_session

# Initialize authentication session
restore_session()

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