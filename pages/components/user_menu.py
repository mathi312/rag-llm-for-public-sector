import streamlit as st
from extensions.user import User
from extensions.pocketbase import logout_user
from extensions.app_session import reset_chat_context

def user_menu(user: User) -> None:
    """Render a user menu with profile info and logout option."""
    
    display_name = user.name or user.email

    # User menu expander
    with st.expander(f"**{display_name}**", expanded=False):
        st.write("")
        st.markdown(f"**Email:** {user.email}")

        if user.is_admin:
            st.markdown("**Role:** Admin")

        st.write("")
        if st.button(
            "Logout",
            key="logout_btn",
            use_container_width=True,
            type="primary"
        ):
            logout_user()
            reset_chat_context(st)
            st.switch_page("pages/ragllm.py")
