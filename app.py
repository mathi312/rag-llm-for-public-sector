import streamlit as st
from extensions.app_session import initialize_app_session
from extensions.pocketbase import is_authenticated, restore_session, user_is_admin
from extensions.pocketbase.pocketbase_browser_session import PocketBaseBrowserSession

# Initialize authentication session
browser_session = PocketBaseBrowserSession(st)
initialize_app_session(st)

if browser_session.clear_pending():
    browser_session.flush_clear()
    st.session_state.pop("pb_auth", None)
    st.session_state.pop("user", None)
else:
    restore_session()
    browser_session.sync_auth(st.session_state.get("pb_auth"))

# Define the pages
pages: dict[str, list[st.Page]] = {}

pages["RAG-LLM"] = [st.Page("pages/ragllm.py", title="RAG-LLM")]

if not is_authenticated():
    pages["User"] = [
        st.Page("pages/authentication/login.py", title="Login"),
    ]

if is_authenticated() and user_is_admin():
    pages["Logs"] = [st.Page("pages/log/loggerview.py", title="Logs")]
    pages["Documentmanager"] = [
        st.Page("pages/management/documents.py", title="Document Manager"),
        st.Page("pages/views/pdf_view.py", title="PDF View"),
    ]

page_navigation = st.navigation(pages, position="top")
page_navigation.run()
