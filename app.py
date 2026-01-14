import streamlit as st
from extensions.pocketbase import is_authenticated, logout_user, restore_session

# Initialize authentication session
restore_session()


def on_logout() -> None:
    logout_user()


# Define the pages
pages: dict[str, list[st.Page]] = {}

pages["RAG-LLM"] = [st.Page("pages/ragllm.py", title="RAG-LLM")]

if not is_authenticated():
    pages["User"] = [
        st.Page("pages/authentication/login.py", title="Login"),
    ]

if is_authenticated():
    _, btn_col = st.columns([6, 1])
    with btn_col:
        st.button("Logout", on_click=on_logout, type="primary")

page_navigation = st.navigation(pages, position="top")
page_navigation.run()
