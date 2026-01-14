import streamlit as st
import re
from extensions.pocketbase import *
from extensions.pocketbase_messages import PBError, PBWarning, PBSuccess

st.set_page_config(page_title="Login", layout="centered")

st.title("Login")
st.caption("Enter your credentials below.")

with st.form("login_form"):
    email = st.text_input("E-Mail")
    password = st.text_input("Password", type="password")
    remember = st.checkbox("Remember me", value=True)

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
                client.auth_store.save(auth_result.token, auth_result.record)

                if remember:
                    st.session_state["pb_auth"] = {
                        "token": auth_result.token,
                        "model": auth_result.record,
                    }
                st.success(PBSuccess.AUTHENTICATION_SUCCESS.value)
                st.switch_page("pages/ragllm.py")
            else:
                st.error(PBError.AUTHENTICATION_FAILED.value)
