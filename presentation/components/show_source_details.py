import streamlit as st

# --- Dialog to display the source ---
@st.dialog("Source Content")
def show_source_details(content, title):
    st.write(f"### {title}")
    st.write("---")
    st.write(content)
    if st.button("Close"):
        st.rerun()
