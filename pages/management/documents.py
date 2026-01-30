import streamlit as st
from extensions.documentupload import (
    upload_document,
    list_documents,
    delete_document,
    update_document,
)

st.set_page_config(page_title="Document Management", layout="wide")

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
    columns = [2, 1, 2, 3, 1, 1, 0.5, 0.5]

    cols = st.columns(columns)
    cols[0].markdown("**Title**")
    cols[1].markdown("**Version**")
    cols[2].markdown("**Needed IDs**")
    cols[3].markdown("**Document**")
    cols[4].markdown("**Created**")
    cols[5].markdown("**Updated**")
    cols[6].markdown("**Actions**")
    cols[7].markdown("")

    st.divider()

    for doc in docs:
        cols = st.columns(columns)
        # Title
        cols[0].markdown(f"**{doc.get('title','')}**")

        # Version
        cols[1].markdown(f"v{doc.get('version','')}")

        # Needed IDs
        cols[2].markdown(", ".join(doc.get("needed_id", [])) or "\-")

        # Document
        cols[3].markdown(f"{doc.get('document','')}")

        # Created
        cols[4].markdown(f"{doc.get('created','')}")

        # Updated
        cols[5].markdown(f"{doc.get('updated','')}")

        # Edit
        if cols[6].button("✏️ Edit", key=f"edit-{doc['id']}"):
            update_document(
                record_id=doc["id"],
                title=doc.get("title"),
                version=doc.get("version") + 1,
                needed_id=doc.get("needed_id"),
            )

        # Delete
        if cols[7].button("🗑️ Delete", key=f"del-{doc['id']}"):
            if delete_document(
                doc["id"],
                document_name=doc.get("document"),
                original_name=doc.get("original_name"),
            ):
                st.success("Dokument gelöscht.")
                st.rerun()

        st.divider()
else:
    st.info("Keine Dokumente vorhanden.")

# TODO: Wenn ein Dokument aktualisiert wird, wird geprüft, ob der Dateiname geändert wurde. Dieser muss identisch zum vorherhigen Dateinamen bleiben. 
# TODO: Wenn ein Dokument aktualisiert wird, darf die Versionsnummer nicht manuell geändert werden, sondern muss automatisch um 1 erhöht werden.
# TODO: Tests schreiben für documentupload.py Funktionen: upload_document, list_documents, delete_document, update_document
