import streamlit as st
from pathlib import Path

st.set_page_config(page_title="PDF Detail View", layout="wide")

def clear_pdf_state_and_return() -> None:
    st.session_state.pop("pdf_view_name", None)
    st.switch_page("pages/management/documents.py")

# Guard: prevent direct navigation
name = st.session_state.get("pdf_view_name")
if not name:
    st.error("Direct access is not allowed.")
    st.switch_page("pages/management/documents.py")
    st.stop()

st.header("PDF Detail View")

# Back button (clears state)
if st.button("Return To Documents"):
    clear_pdf_state_and_return()

data_dir = Path(__file__).resolve().parent.parent.parent / "data"
file_path = data_dir / name

if not file_path.exists():
    st.error("File not found.")
    st.stop()

if file_path.suffix.lower() != ".pdf":
    st.info("Only PDF files can be displayed.")
    st.stop()

st.pdf(str(file_path), height=900)