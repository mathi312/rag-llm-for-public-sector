import streamlit as st
import re
from extensions.pocketbase import authenticate_user
from extensions.pocketbase.pocketbase_messages import PBError, PBWarning, PBSuccess, PBLog
from extensions.user import User
from extensions.pocketbase import pb_url

st.set_page_config(page_title="Login", layout="centered")

st.title("Login")
st.caption("Enter your credentials below.")

with st.form("login_form"):
    email = st.text_input("E-Mail")
    password = st.text_input("Password", type="password")

    submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
        if not email.strip() or not password:
            st.warning(PBWarning.MISSING_CREDENTIALS.value)
        elif not re.match(email_pattern, email):
            st.warning(PBWarning.INCORRECT_EMAIL_FORMAT.value)
        else:
            auth_result = authenticate_user(email, password)
            if auth_result != PBError.AUTHENTICATION_FAILED.name:
                st.success(PBSuccess.AUTHENTICATION_SUCCESS.value)
                st.rerun()
            else:
                st.error(PBError.AUTHENTICATION_FAILED.value)
