import os
import streamlit as st
from pocketbase import PocketBase
from extensions.pberrors import PBError

pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
client = PocketBase(pb_url)

def authenticate_user(email: str, password: str):
    """Authenticate a user with PocketBase."""
    try:
        auth_data = client.collection('users').auth_with_password(email, password)
        return auth_data
    except Exception as e:
        return PBError.AUTHENTICATION_FAILED.name
    
def logout_user():
    """Logout the current user."""
    client.auth_store.clear()

def is_logged_in():
    is_logged_in = bool(client.auth_store.token)
    if is_logged_in and client.auth_store.model:
        name = (
            getattr(client.auth_store.model, "name", None)
        )
        st.success(f"Eingeloggt als: {name or 'Unbekannt'}")
        st.text(f"Admin: {'Ja' if user_is_admin() else 'Nein'}")
        st.button("Logout", on_click=logout_user)
    else:
        st.info("Nicht eingeloggt")
        open_login_dialog()

def user_is_admin() -> bool:
    model = client.auth_store.model

    if not model:
        return False
    
    if hasattr(model, "get"):
        return bool(
            model.get("admin")
        )
    
    return bool(
        getattr(model, "admin", False)
    )

def open_login_dialog():
    """Open the login dialog"""
    @st.dialog("Login")
    def login():
        st.write("Bitte melden Sie sich an:")
        with st.form('login_form'):
            email = st.text_input("E-Mail")
            password = st.text_input("Passwort", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                auth_result = authenticate_user(email, password)
                if auth_result != PBError.AUTHENTICATION_FAILED.name:
                    st.success("Erfolgreich eingeloggt!")
                    st.rerun()
                else:
                    st.error("Login fehlgeschlagen. Bitte überprüfen Sie Ihre Anmeldedaten.")
                
    if st.button("Login"):
        login()