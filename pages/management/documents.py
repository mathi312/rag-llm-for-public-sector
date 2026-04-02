import streamlit as st
from extensions.documents.documentupload import (
    upload_document,
    list_documents,
    update_document,
    confirm_delete_document,
    view_pdf_dialog,
)
from extensions.predefined_questions.question_controller import generate_questions
from extensions.documents.document_management_controller import DocumentManagementController
from pages.management.dialogs.show_questions_dialog import show_questions_dialog

st.set_page_config(page_title="Document Management", layout="wide")

# Initialize loading state
if "generating_for" not in st.session_state:
    st.session_state.generating_for = None
if "pending_questions" in st.session_state:
    questions_to_show = st.session_state.pop("pending_questions")
    show_questions_dialog(questions_to_show)
    
controller = DocumentManagementController(
    streamlit_module=st,
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

is_loading = st.session_state.generating_for is not None

if st.button("Upload New Document", disabled=is_loading):
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
        doc_id = doc["id"]
        is_this_loading = st.session_state.generating_for == doc_id

        # Title
        cols[0].markdown(f"**{doc.get('title','')}**")

        # Version
        cols[1].markdown(f"v{doc.get('version','')}")

        # Needed IDs
        cols[2].markdown(", ".join(doc.get("needed_id", [])) or "-")

        # Document
        cols[3].markdown(f"{doc.get('original_name','')}")

        # Created
        cols[4].markdown(f"{doc.get('created','')}")

        # Updated
        cols[5].markdown(f"{doc.get('updated','')}")

        # Generate questions — shows spinner label while loading
        if cols[6].button(
            "Generate questions",
            key=f"generate-{doc_id}",
            use_container_width=True,
            disabled=is_loading,
        ):
            st.session_state.generating_for = doc_id  # set loading state
            st.rerun()

        # View
        if cols[7].button(
            "👁️ View", 
            key=f"view-{doc['id']}", 
            use_container_width=True, 
            disabled=is_loading
        ):
            controller.handle_view(doc)

        # Edit
        if cols[8].button(
            "✏️ Edit",
            key=f"edit-{doc['id']}",
            use_container_width=True,
            disabled=is_loading,
        ):
            controller.handle_edit(doc)

        # Delete
        if cols[9].button(
            "🗑️ Delete",
            key=f"del-{doc['id']}",
            use_container_width=True,
            disabled=is_loading
        ):
            controller.handle_delete(doc)

        st.divider()

    # --- Run generation after re-render (buttons are now disabled) ---
    if st.session_state.generating_for is not None:
        generating_doc = next((d for d in docs if d["id"] == st.session_state.generating_for), None)
        if generating_doc:
            with st.spinner(
                f"Generating questions for **{generating_doc.get('original_name')}**..."
            ):
                questions = generate_questions(
                    document_name=generating_doc.get("original_name"),
                    provider=st.session_state.get("provider") or "Local (Ollama)",
                    model_name=st.session_state.get("selected_model") or "llama3.2",
                )
            st.session_state.generating_for = None  # clear loading state
            if questions:
                st.session_state.pending_questions = questions
            else:
                st.error(
                    f"Could not generate questions for **{generating_doc.get('original_name')}**." +
                    "Please try again later."
                )
            st.rerun()

else:
    st.info("Keine Dokumente vorhanden.")
