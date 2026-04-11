import streamlit as st

from application.idprovider import IdType, process_id_document

# helper to handle the upload of an id
def handle_id_upload(id_image, id_type: IdType | None = None):
    # rewind to start of file, needed when trying to process the image a second time
    id_image.seek(0)

    extracted_data = process_id_document(
        id_image.read(),
        id_type=id_type
    )
    st.session_state["id_uploaded"] = True

    st.session_state["id_document"] = {
        "type": extracted_data.get("id_type").value,
        "data": extracted_data,
    }


@st.dialog("Manually select your id type")
def select_id_type_dialog(id_image, exception: str):
    st.error(exception)
    st.write("Please manually select the ID type you provided.")

    selected_id_type = st.selectbox(
        "Select Citizen ID",
        options=list(IdType),
        index=0,
        format_func=lambda x: x.value
    )

    if st.button("Process ID Document Again"):
        try:
            handle_id_upload(id_image, selected_id_type)

            st.success("ID Document successfully processed!")
        except Exception as exc:
            st.error(f"OCR processing failed: {exc}")
