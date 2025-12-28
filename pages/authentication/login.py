import streamlit as st

st.set_page_config(page_title="Login", layout="centered")


def validate_login(email: str, password: str) -> tuple[bool, str | None]:
	if not email or not password:
		return False, "Bitte fülle alle Felder aus."



st.title("Anmeldung")
st.caption("Gib deine Zugangsdaten unten ein.")

if "auth_user" not in st.session_state:
	st.session_state.auth_user = None

if st.session_state.auth_user:
	st.success(f"Bereits angemeldet als {st.session_state.auth_user['email']}")
	if st.button("Abmelden", type="secondary"):
		st.session_state.auth_user = None
		st.rerun()
	st.stop()



with st.form("login_form"):
    email = st.text_input("E-Mail", placeholder="you@example.com")
    password = st.text_input("Passwort", type="password", placeholder="password123")
    remember = st.checkbox("Angemeldet bleiben", value=True)

    submitted = st.form_submit_button("Anmelden", use_container_width=True)

    if submitted:
        ok, error = validate_login(email, password)
        if ok:
            st.session_state.auth_user = {"email": email.strip(), "remember": remember}
            st.success("Login erfolgreich. Willkommen zurück!")
            st.rerun()
        else:
            st.error(error)
