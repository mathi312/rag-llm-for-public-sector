import streamlit as st

from application.predefined_questions import get_questions, update_times_asked_of_question

if "example_questions" not in st.session_state:
    st.session_state.example_questions = get_questions()

def refresh_questions():
    questions = get_questions(random=True)
    if questions:
        st.session_state.example_questions = questions
    else:
        st.session_state.questions_error = True


def render_suggestions():
    st.button("🔄 New Questions", on_click=refresh_questions)

    if st.session_state.pop("questions_error", False):
        st.error("Could not refresh questions. Please try again later.")

    if not st.session_state.get("example_questions"):
        st.info("No questions available right now. Please refresh or try again later.")
        return

    st.markdown("#### How can I help you today?")
    cols = st.columns(3)

    for i, q in enumerate(st.session_state.example_questions):
        with cols[i % 3]:
            if st.button(q.question, key=f"suggest-{q.id}"):
                st.session_state["prefill"] = q.question
                st.session_state["auto_send"] = True
                update_times_asked_of_question(q.id)
