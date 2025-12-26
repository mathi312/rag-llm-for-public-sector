import streamlit as st
import re

st.set_page_config(page_title="Registrierung", page_icon="📝", layout="centered")

st.title("Registrieren")
st.caption("Demo-Registrierung (ohne Persistenz)")

with st.form("register_form", clear_on_submit=False):
    username = st.text_input("Benutzername", max_chars=50)
    email = st.text_input("E-Mail", max_chars=120, placeholder="name@example.com")
    password = st.text_input("Passwort", type="password")
    password_confirm = st.text_input("Passwort bestätigen", type="password")
    submitted = st.form_submit_button("Account anlegen")

def is_valid_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value or ""))

if submitted:
    errors = []
    if not username.strip():
        errors.append("Benutzername darf nicht leer sein.")
    if not is_valid_email(email):
        errors.append("Bitte eine gültige E-Mail eingeben.")
    if len(password) < 6:
        errors.append("Passwort muss mindestens 6 Zeichen lang sein.")
    if password != password_confirm:
        errors.append("Passwörter stimmen nicht überein.")

    if errors:
        st.error("❌ Registrierung fehlgeschlagen:\n- " + "\n- ".join(errors))
    else:
        st.success("✅ Konto erstellt! (Demo: keine Speicherung). Bitte jetzt im Login anmelden.")
        st.info("Hinweis: Ersetze diese Demo-Logik durch dein tatsächliches User-Backend (DB/IDP).")