from typing import List

import streamlit as st

from extensions.question_generator import save_questions_to_pb


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
        key="questions_editor"
    )

    st.divider()

    if st.button("Save Questions"):
        to_save = [row["question"] for row in edited_list if row.get("question")]

        if not to_save:
            st.error("The list is empty. Please add at least one question.")
            return

        try:
            save_questions_to_pb(to_save)
            st.success("Successfully saved questions!")
            # clear seesion state
            del st.session_state.questions
            if "questions_editor" in st.session_state:
                del st.session_state["questions_editor"]

        except ValueError as e:
            st.warning(e)
        except Exception as exc:
            st.exception(exc)
