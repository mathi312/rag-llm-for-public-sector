import streamlit as st
from pathlib import Path
from config import LOG_DIR
from application.pocketbase import is_authenticated, user_is_admin

st.set_page_config(page_title="Logs", layout="wide")

if not is_authenticated():
    st.error("Authentication required.")
    st.switch_page("pages/authentication/login.py")
    st.stop()

if not user_is_admin():
    st.error("Access denied. Admins only.")
    st.switch_page("pages/ragllm.py")
    st.stop()

st.title("Logdateien")

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_files = sorted(LOG_DIR.glob("*.log"), reverse=True)

@st.dialog("Logdatei löschen")
def confirm_delete():
    st.warning(f"Willst du {selected} wirklich löschen?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ja, löschen", type="primary"):
            selected_path.unlink(missing_ok=True)
            st.success(f"{selected} wurde gelöscht.")
            st.rerun()
    with col2:
        if st.button("Abbrechen"):
            st.info("Löschvorgang abgebrochen.")
            st.rerun()


if not log_files:
    st.info("Keine Logdateien gefunden.")
else:
    file_names: list[str] = [f.name for f in log_files]
    selected: str = st.selectbox("Logdatei auswählen", file_names)

    selected_path: Path = LOG_DIR / selected
    content: str = selected_path.read_text(encoding="utf-8")

    st.subheader(f"Inhalt: {selected}")

    def _color_line(line: str) -> str:
        #Expected formatting: [YYYY-MM-DD HH:MM:SS] [LEVEL] Message
        try:
            timestamp_part, rest = line.split("] ", 1)
            level_part, message = rest.split("] ", 1)
            timestamp = timestamp_part.strip("[]")
            level = level_part.strip("[]")

            level_color = {
                "INFO": "#4FC3F7",
                "WARNING": "#FFB74D",
                "ERROR": "#E57373",
            }.get(level, "#E0E0E0")

            return (
                f"<span style='color:#9E9E9E'>[{timestamp}]</span> "
                f"<span style='color:{level_color}; font-weight:600'>[{level}]</span> "
                f"<span style='color:#FFFFFF'>{message}</span>"
            )
        except ValueError:
            return f"<span style='color:#FFFFFF'>{line}</span>"

    colored_lines = "<br>".join(_color_line(l) for l in content.splitlines())
    st.markdown(
        f"<div style='background:rgb(38, 39, 48);padding:12px; border-radius:6px; font-family:monospace; white-space:pre-wrap; margin-bottom:16px'>{colored_lines}</div>",
        unsafe_allow_html=True,
    )

    st.download_button(
        label="Logdatei herunterladen",
        data=content,
        file_name=selected,
        mime="text/plain",
    )

    if st.button("Logdatei löschen", type="secondary"):
        confirm_delete()
