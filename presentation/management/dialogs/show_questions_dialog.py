from typing import List

import streamlit as st

from application.predefined_questions import save_questions


@st.dialog("Review Generated Questions")
def show_questions_dialog(generated_questions: List[str]):
    """
    Display a list of generated questions.
    """
    st.session_state.questions = [{"question": q} for q in generated_questions]

    st.write("#### Edit your questions below")
    st.caption("Double-click a cell to edit. Select a row and hit 'Backspace' to delete.")

    # st.data_editor stays in sync with its own internal state
    edited_list = st.data_editor(
        st.session_state.questions,
        num_rows="dynamic",
        use_container_width=True,
        key="questions_editor",
    )

    st.divider()

    if st.button("Save Questions"):
        to_save = [
            row["question"].strip()
            for row in edited_list
            if row.get("question") is not None
            and isinstance(row["question"], str)
            and row["question"].strip()
        ]

        if not to_save:
            st.error("The list is empty. Please add at least one question.")
            return

        if save_questions(to_save):
            st.success("Successfully saved questions!")
            del st.session_state.questions
            if "questions_editor" in st.session_state:
                del st.session_state["questions_editor"]
        else:
            st.error("Could not save questions. Please try again later.")
