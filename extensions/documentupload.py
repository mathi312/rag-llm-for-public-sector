import os
import tempfile
import mimetypes
from pathlib import Path
from pocketbase import PocketBase
from pocketbase.client import FileUpload
import streamlit as st


# def upload_document(file_path: str) -> FileUpload:

pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
client = PocketBase(pb_url)

client.admins.auth_with_password(
    os.getenv("POCKETBASE_ADMIN_USERNAME"), os.getenv("POCKETBASE_ADMIN_PASSWORD")
)


@st.dialog("Upload Document")
def upload_document():
    """Upload a document to PocketBase and return the FileUpload info."""
    title = st.text_input("Document Title")
    version = st.text_input("Document Version", value="1")
    needed_id = st.multiselect(
        "Select Needed IDs", options=["id-card", "residence-permit", "passport"]
    )
    uploaded_file = st.file_uploader(
        "Choose a document to upload", type=["pdf", "docx"]
    )
    if st.button("Upload") and uploaded_file:
        with st.spinner("Uploading document..."):
            temp_file_path = Path(tempfile.gettempdir()) / uploaded_file.name
            data_dir = Path(__file__).resolve().parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            try:
                with open(temp_file_path, "wb") as temp_file:
                    temp_file.write(uploaded_file.getvalue())

                client.collection("documents").create(
                    {
                        "title": title,
                        "version": version,
                        "needed_id": needed_id,
                        "original_name": uploaded_file.name,
                        "document": FileUpload(
                            (
                                str(temp_file_path),
                                uploaded_file.name,
                                uploaded_file.type or "application/octet-stream",
                            )
                        ),
                    }
                )

                dest_path = data_dir / uploaded_file.name
                with open(temp_file_path, "rb") as src, open(dest_path, "wb") as dst:
                    dst.write(src.read())

                st.session_state["upload_success_msg"] = (
                    "Dokument erfolgreich hochgeladen."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Failed to upload document: {e}")
            finally:
                if temp_file_path.exists():
                    temp_file_path.unlink()
    return None


def list_documents() -> list[dict]:
    """List all documents from PocketBase."""
    try:
        records = client.collection("documents").get_full_list()
        return [
            {
                "id": r.id,
                "title": getattr(r, "title", None),
                "version": getattr(r, "version", None),
                "needed_id": getattr(r, "needed_id", None),
                "original_name": getattr(r, "original_name", None),
                "document": getattr(r, "document", None),
                "created": getattr(r, "created", None),
                "updated": getattr(r, "updated", None),
            }
            for r in records
        ]
    except Exception as e:
        st.error(f"Failed to fetch documents: {e}")
        return []


def delete_document(
    record_id: str, document_name: str | None = None, original_name: str | None = None
) -> bool:
    """Delete a document record and remove matching files from data/."""
    data_dir = Path(__file__).resolve().parent.parent / "data"
    processed = False
    try:
        client.collection("documents").delete(record_id)
        processed = True
    except Exception as e:
        st.error(f"Failed to delete document: {e}")
    for name in {document_name, original_name}:
        if name:
            path = data_dir / name
            if path.exists():
                try:
                    path.unlink()
                except Exception as e:
                    st.warning(f"Konnte Datei {name} nicht löschen: {e}")
    return processed


@st.dialog("Update Document")
def update_document(
    record_id: str,
    title: str | None = None,
    version: str | None = None,
    needed_id: list[str] | None = None,
    file_path: str | None = None,
) -> bool:

    title = st.text_input("Document Title", value=title or "")
    version = st.text_input("Document Version", value=version or "")
    needed_id = st.multiselect(
        "Select Needed IDs",
        options=["id-card", "residence-permit", "passport"],
        default=needed_id or [],
    )
    uploaded_file = st.file_uploader(
        "Choose a document to upload", type=["pdf", "docx"]
    )

    if st.button("Update"):
        payload: dict = {}
        if title:
            payload["title"] = title
        if version:
            payload["version"] = version
        if needed_id is not None:
            payload["needed_id"] = needed_id

        temp_file_path = None
        data_dir = Path(__file__).resolve().parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        try:
            local_path = None
            fname = None
            mime = None

            if uploaded_file:
                temp_file_path = Path(tempfile.gettempdir()) / uploaded_file.name
                with open(temp_file_path, "wb") as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                local_path = temp_file_path
                fname = uploaded_file.name
                mime = uploaded_file.type or "application/octet-stream"
                payload["original_name"] = fname
            elif file_path:
                local_path = Path(file_path)
                fname = local_path.name
                mime = mimetypes.guess_type(fname)[0] or "application/octet-stream"

            if local_path:
                payload["document"] = FileUpload((str(local_path), fname, mime))

            client.collection("documents").update(record_id, payload)

            # Datei auch in data/ aktualisieren, falls wir eine neue haben
            if local_path and local_path.exists():
                dest_path = data_dir / fname
                with open(local_path, "rb") as src, open(dest_path, "wb") as dst:
                    dst.write(src.read())

            st.session_state["upload_success_msg"] = "Dokument aktualisiert."
            st.rerun()
        except Exception as e:
            st.error(f"Failed to update document: {e}")
            return False
        finally:
            if temp_file_path and Path(temp_file_path).exists():
                Path(temp_file_path).unlink()
    return False
