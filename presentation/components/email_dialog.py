import re
import streamlit as st

from application.report_generator import send_report_via_email
from domain.report.excpetions import EmptyEmailAddressError, EmptyReportError

# Dialog for entering a email address
@st.dialog("Enter your email address")
def email_dialog(exception: str):
    st.error(exception)
    st.write("Please provide your email to receive the report.")
    email = st.text_input("Email")

    if st.button("Send email"):
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
        if not re.match(email_pattern, email):
            st.warning("Invalid email address")
        else:
            try:
                send_report_via_email(st.session_state.report, email, st.session_state.user)
                st.success("Email sent successfully.")
            except (EmptyReportError, EmptyEmailAddressError) as e:
                st.warning(str(e))
            except Exception as e:
                st.exception(e)
