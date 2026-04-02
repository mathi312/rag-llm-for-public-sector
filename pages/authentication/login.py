import streamlit as st
import re
from extensions.pocketbase import authenticate_user
from extensions.pocketbase.pocketbase_messages import PBError, PBWarning, PBSuccess, PBLog
from extensions.user import User
from extensions.logger import Logger
from extensions.pocketbase.pocketbase_client import get_pocketbase_client

pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")

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
                user = User.from_pb_record(auth_result.record)
                st.session_state.user = user
                st.session_state["pb_auth"] = {
                    "token": auth_result.token,
                    "model": auth_result.record,
                }

                # Also save to PocketBase auth_store for persistence across page reloads
                pb_client = PocketBase(pb_url)
                auth_store = getattr(pb_client, "auth_store", None)
                if auth_store and hasattr(auth_store, "save"):
                    try:
                        auth_store.save(auth_result.token, auth_result.record)
                    except Exception as e:
                        logger.log_warning(PBLog.SAVE_AUTH_TO_STORE_FAILED.value.format(error=e))

                logger.log_info(PBLog.USER_LOGGED_IN_SUCCESS.value.format(email=user.email))

                st.success(PBSuccess.AUTHENTICATION_SUCCESS.value)
                st.rerun()
            else:
                st.error(PBError.AUTHENTICATION_FAILED.value)
