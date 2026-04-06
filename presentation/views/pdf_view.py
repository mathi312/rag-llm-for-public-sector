import streamlit as st
from pathlib import Path
from application.pocketbase import is_authenticated, user_is_admin

st.set_page_config(page_title="PDF Detail View", layout="wide")

def clear_pdf_state_and_return() -> None:
    st.session_state.pop("pdf_view_name", None)
    st.switch_page("presentation/management/documents.py")

# Guard: prevent direct navigation
name = st.session_state.get("pdf_view_name")
if not name:
    st.error("Direct access is not allowed.")
    st.switch_page("presentation/management/documents.py")
    st.stop()

if not is_authenticated():
    st.error("Authentication required.")
    st.switch_page("presentation/authentication/login.py")
    st.stop()

if not user_is_admin():
    st.error("Access denied. Admins only.")
    st.switch_page("presentation/ragllm.py")
    st.stop()

st.header("PDF Detail View")

# Back button (clears state)
if st.button("Return To Documents"):
    clear_pdf_state_and_return()

data_dir = Path(__file__).resolve().parent.parent.parent / "data"
file_path = (data_dir / name).resolve()

if data_dir.resolve() not in file_path.parents:
    st.error("Invalid file path.")
    st.stop()

if not file_path.exists():
    st.error("File not found.")
    st.stop()

if file_path.suffix.lower() != ".pdf":
    st.info("Only PDF files can be displayed.")
    st.stop()

st.pdf(str(file_path), height=900)
