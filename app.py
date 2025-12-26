import streamlit as st

pages = {
    "RAG-LLM": [
        st.Page("pages/ragllm.py", title="RAG-LLM")
    ],
    "User": [
        st.Page("pages/authentication/login.py", title="Login"),
        st.Page("pages/authentication/register.py", title="Register")
    ],
    # "User Management": [
    #     st.Page("pages/usermanagement.py", title="User Management")
    # ]
}

page_navigation = st.navigation(pages, position="top")
page_navigation.run()