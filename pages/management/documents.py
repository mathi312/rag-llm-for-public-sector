import streamlit as st
from extensions.documents.documentupload import (
    upload_document,
    list_documents,
    update_document,
    confirm_delete_document,
    view_pdf_dialog,
)
from extensions.documents.document_management_controller import DocumentManagementController
from extensions.example_questions.question_controller import generate_questions
from pages.management.dialogs.show_questions_dialog import show_questions_dialog

st.set_page_config(page_title="Document Management", layout="wide")

controller = DocumentManagementController(
    streamlit_module=st,
    generate_questions_fn=generate_questions,
    show_questions_dialog_fn=show_questions_dialog,
    view_pdf_dialog_fn=view_pdf_dialog,
    update_document_fn=update_document,
    confirm_delete_document_fn=confirm_delete_document,
)

if st.session_state.get("upload_success_msg"):
    st.toast(st.session_state["upload_success_msg"])
    del st.session_state["upload_success_msg"]

# upload document dialog
st.header("3. Document Management")
if st.button("Upload New Document"):
    upload_document()

# Show existing documents
docs = list_documents()
if docs:
    columns = [2, 1, 2, 3, 1, 1, 1, 1, 1, 1]

    cols = st.columns(columns, gap="small")
    cols[0].markdown("**Title**")
    cols[1].markdown("**Version**")
    cols[2].markdown("**Needed IDs**")
    cols[3].markdown("**Document**")
    cols[4].markdown("**Created**")
    cols[5].markdown("**Updated**")
    cols[6].markdown("**Actions**")
    cols[7].markdown("")
    cols[8].markdown("")
    cols[9].markdown("")

    st.divider()

    for doc in docs:
        cols = st.columns(columns, gap="small")
        # Title
        cols[0].markdown(f"**{doc.get('title','')}**")

        # Version
        cols[1].markdown(f"v{doc.get('version','')}")

        # Needed IDs
        cols[2].markdown(", ".join(doc.get("needed_id", [])) or "\-")

        # Document
        cols[3].markdown(f"{doc.get('original_name','')}")

        # Created
        cols[4].markdown(f"{doc.get('created','')}")

        # Updated
        cols[5].markdown(f"{doc.get('updated','')}")

        # generate example questions
        if cols[6].button("Generate questions", key=f"generate-{doc['id']}", use_container_width=True):
            controller.handle_generate_questions(doc)

        # View
        if cols[7].button("👁️ View", key=f"view-{doc['id']}", use_container_width=True):
            controller.handle_view(doc)

        # Edit
        if cols[8].button("✏️ Edit", key=f"edit-{doc['id']}", use_container_width=True):
            controller.handle_edit(doc)

        # Delete
        if cols[9].button("🗑️ Delete", key=f"del-{doc['id']}", use_container_width=True):
            controller.handle_delete(doc)

        st.divider()
else:
    st.info("Keine Dokumente vorhanden.")