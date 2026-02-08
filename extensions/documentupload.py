import os
import tempfile
import mimetypes
from pathlib import Path
from pocketbase import PocketBase
from pocketbase.client import FileUpload
import streamlit as st
import difflib
from pypdf import PdfReader
import docx2txt
import shutil
import re
from datetime import datetime

pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
client = PocketBase(pb_url)

client.admins.auth_with_password(
    os.getenv("POCKETBASE_ADMIN_USERNAME"), os.getenv("POCKETBASE_ADMIN_PASSWORD")
)


@st.dialog("Upload Document")
def upload_document():
    """Upload a document to PocketBase and return the FileUpload info."""
    title = st.text_input("Document Title")
    version = st.text_input("Document Version", value="1", disabled=True)
    needed_id = st.multiselect(
        "Select Needed IDs", options=["id-card", "residence-permit", "passport"]
    )
    uploaded_file = st.file_uploader(
        "Choose a document to upload", type=["pdf", "docx"]
    )

    title_filled = bool(title and title.strip())

    identical = False
    file_bytes = None

    # Check for identical or similar documents before allowing upload, to prevent duplicates and provide user feedback on potential matches.
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        temp_file_path = Path(tempfile.gettempdir()) / uploaded_file.name
        data_dir = Path(__file__).resolve().parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save the uploaded file to a temporary location for comparison
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(file_bytes)

            is_identical, similar = compare_with_existing_documents(
                temp_file_path, data_dir, similarity_threshold=0.85
            )
            if is_identical:
                identical = True
                st.error(
                    "Upload aborted: Content is identical to an existing document."
                )

            if similar:
                p, ratio, diff = similar
                st.warning(
                    f"Similar document found: {p.name} (Similarity: {ratio:.0%})."
                )
                with st.expander("Show diff"):
                    st.code(diff or "No diff available.", language="diff")
        finally:
            # Cleanup temp file
            if temp_file_path.exists():
                temp_file_path.unlink()

    if (
        st.button("Upload", disabled=identical or not uploaded_file or not title_filled)
        and uploaded_file
    ):
        if not title_filled:
            st.error("Bitte einen Titel eingeben.")
            return None
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
                    "Document uploaded successfully."
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


@st.dialog("Confirm Delete Document")
def confirm_delete_document(
    record_id: str,
    document_name: str | None = None,
    original_name: str | None = None,
) -> bool:
    """Show a confirmation dialog to delete a document, and if confirmed, proceed to remove it."""
    st.warning("Do you really want to delete this document?")
    if original_name or document_name:
        st.caption(f"File: {original_name or document_name}")
    col1, col2 = st.columns(2, gap="small")
    with col1:
        if st.button("Yes, delete", use_container_width=True):
            ok = delete_document(
                record_id=record_id,
                document_name=document_name,
                original_name=original_name,
            )
            if ok:
                st.session_state["upload_success_msg"] = "Document deleted."
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    return False


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
                    st.warning(f"Could not delete file {name}: {e}")
    return processed


def extract_text_from_file(file_path: Path) -> str:
    """Extract text content from a pdf or docx file."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        return docx2txt.process(str(file_path)) or ""
    # Fallback: bytes -> string (ignoring errors)
    try:
        return file_path.read_bytes().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def build_diff(fst_text: str, snd_text: str, fromfile: str, tofile: str) -> str:
    """Build a unified diff string between two texts (in this case two documents content)."""
    fst_lines = fst_text.splitlines()
    snd_lines = snd_text.splitlines()
    diff = difflib.unified_diff(
        fst_lines, snd_lines, fromfile=fromfile, tofile=tofile, lineterm=""
    )
    return "\n".join(diff)


def compare_with_existing_documents(
    new_file_path: Path,
    data_dir: Path,
    similarity_threshold: float = 0.85,
) -> tuple[bool, tuple[Path, float, str] | None]:
    """
    Compare the content of a new document with existing documents in the data directory,
    returning whether an identical match was found and the best similar match if not.
    """
    new_text = extract_text_from_file(new_file_path).strip()
    if not new_text:
        return False, None

    best_match: tuple[Path, float, str] | None = None

    for path in data_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".docx"}:
            continue

        old_text = extract_text_from_file(path).strip()
        if not old_text:
            continue

        if old_text == new_text:
            return True, None

        ratio = difflib.SequenceMatcher(None, old_text, new_text).ratio()
        # If the similarity ratio exceeds the threshold, we consider it a similar document and prepare a diff for user review.
        if ratio >= similarity_threshold:
            diff = build_diff(
                old_text,
                new_text,
                fromfile=f"ALT: {path.name}",
                tofile=f"NEU: {new_file_path.name}",
            )
            # Keep track of the best match (highest similarity ratio) for potential user feedback
            if best_match is None or ratio > best_match[1]:
                best_match = (path, ratio, diff)

    return False, best_match


def get_backup_dir() -> Path:
    """Get the backup directory path, creating it if it doesn't exist."""
    backup_dir = Path(__file__).resolve().parent.parent / "data" / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def make_backup_name(record_id: str, version: str, original_name: str) -> str:
    """Create a backup filename based on record ID, version, and original name."""
    safe_version = str(version).strip().replace(" ", "_")
    return f"{record_id}_v{safe_version}_{original_name}"


def parse_backup_name(record_id: str, filename: str) -> tuple[str, str] | None:
    """Parse a backup filename to extract version and original name, ensuring it matches the expected pattern."""
    pattern = (
        rf"^{re.escape(record_id)}_v(.+?)_(.+)$"  # {record_id}_vVERSION_ORIGINALNAME
    )
    m = re.match(pattern, filename)
    if not m:
        return None
    return m.group(1), m.group(2)


@st.dialog("Update Document")
def update_document(
    record_id: str,
    title: str | None = None,
    version: str | None = None,
    needed_id: list[str] | None = None,
    file_path: str | None = None,
    original_name: str | None = None,
    document_name: str | None = None,
    current_version: str | None = None,
) -> bool:
    """Update a document record with new metadata and/or a new file, while handling versioning and backups."""
    orig_title = title or ""
    orig_version = version or ""
    orig_needed_id = needed_id or []

    title = st.text_input("Document Title", value=orig_title)
    version = st.text_input("Document Version", value=orig_version, disabled=True)
    needed_id = st.multiselect(
        "Select Needed IDs",
        options=["id-card", "residence-permit", "passport"],
        default=orig_needed_id,
    )
    uploaded_file = st.file_uploader(
        "Choose a document to upload", type=["pdf", "docx"]
    )

    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = get_backup_dir()

    # Determine existing file path for diffing
    existing_name = original_name or document_name
    existing_path = data_dir / existing_name if existing_name else None

    diff_text = ""
    identical = False
    if uploaded_file and existing_path and existing_path.exists():
        temp_compare_path = Path(tempfile.gettempdir()) / uploaded_file.name
        with open(temp_compare_path, "wb") as temp_file:
            temp_file.write(uploaded_file.getvalue())

        old_text = extract_text_from_file(existing_path)
        new_text = extract_text_from_file(temp_compare_path)
        identical = old_text.strip() == new_text.strip()

        if not identical:
            diff_text = build_diff(
                old_text,
                new_text,
                fromfile=f"ALT: {existing_path.name}",
                tofile=f"NEU: {uploaded_file.name}",
            )

        # Cleanup temp file
        if temp_compare_path.exists():
            temp_compare_path.unlink()

        if identical:
            st.info("The uploaded file is identical in content. Update not possible.")
        else:
            with st.expander("Show Changes"):
                st.code(diff_text or "No diff generated.", language="diff")

    confirm_update = st.checkbox(
        "Allow update (Please review and confirm changes)",
        value=False,
        disabled=identical or not uploaded_file,
    )

    show_version_list(
        record_id=record_id,
        current_version=current_version or "current",
        existing_path=existing_path,
        data_dir=data_dir,
        backup_dir=backup_dir,
        client=client,
    )

    ids_changed = set(needed_id or []) != set(orig_needed_id or [])
    title_changed = title != orig_title
    changed = title_changed or ids_changed or bool(uploaded_file)

    if not changed:
        st.info("No changes detected. Update is disabled.")

    update_disabled = (
        (not changed)
        or bool(uploaded_file and identical)
        or (bool(uploaded_file) and not confirm_update)
    )

    if st.button("Update", disabled=update_disabled):
        if uploaded_file and (identical or not confirm_update):
            st.warning(
                "Update aborted. Your document is identical in content or changes were not confirmed."
            )
            return False

        payload: dict = {}
        if title:
            payload["title"] = title
        if version:
            payload["version"] = version
        if needed_id is not None:
            payload["needed_id"] = needed_id

        temp_file_path = None

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

            # Move old file to backup before updating
            old_name = original_name or document_name
            if old_name:
                old_path = data_dir / old_name
                if old_path.exists():
                    backup_name = make_backup_name(
                        record_id, current_version or "current", old_path.name
                    )
                    shutil.move(str(old_path), str(backup_dir / backup_name))

            client.collection("documents").update(record_id, payload)

            # save new file to data/ if it was uploaded
            if local_path and local_path.exists():
                dest_path = data_dir / fname
                with open(local_path, "rb") as src, open(dest_path, "wb") as dst:
                    dst.write(src.read())

            st.session_state["upload_success_msg"] = "Document updated."
            st.rerun()
        except Exception as e:
            st.error(f"Failed to update document: {e}")
            return False
        finally:
            if temp_file_path and Path(temp_file_path).exists():
                Path(temp_file_path).unlink()
    return False


def show_version_list(
    record_id: str,
    current_version: str,
    existing_path: Path,
    data_dir: Path,
    backup_dir: Path,
    client: PocketBase,
) -> None:
    """Show a list of backup versions for a document and allow restoring a previous version."""
    backup_files = []
    for p in backup_dir.iterdir():
        if p.is_file() and p.name.startswith(f"{record_id}_v"):
            parsed = parse_backup_name(record_id, p.name)
            if parsed:
                backup_files.append((p, parsed[0], parsed[1]))

    if backup_files:
        st.divider()
        st.subheader("Previous Versions")
        table_rows = []
        for p, ver, orig in backup_files:
            table_rows.append(
                {
                    "Version": f"v{ver}",
                    "Filename": orig,
                    "Backup File": p.name,
                    "Date": datetime.fromtimestamp(p.stat().st_mtime).strftime(
                        "%d.%m.%Y %H:%M"
                    ),
                }
            )
        st.dataframe(table_rows, use_container_width=True)

        st.subheader("Restore Previous Version")
        options = [f"v{ver} – {orig} ({p.name})" for p, ver, orig in backup_files]
        idx = st.selectbox(
            "Select Backup", range(len(options)), format_func=lambda i: options[i]
        )
        if st.button("Restore Selected Version"):
            selected_path, selected_version, selected_original = backup_files[idx]

            if existing_path and existing_path.exists():
                backup_name = make_backup_name(
                    record_id, current_version or "current", existing_path.name
                )
                shutil.move(str(existing_path), str(backup_dir / backup_name))

            restored_path = data_dir / selected_original
            shutil.copy2(str(selected_path), str(restored_path))

            try:
                mime = (
                    mimetypes.guess_type(restored_path.name)[0]
                    or "application/octet-stream"
                )
                payload = {
                    "version": selected_version,
                    "original_name": restored_path.name,
                    "document": FileUpload(
                        (str(restored_path), restored_path.name, mime)
                    ),
                }
                client.collection("documents").update(record_id, payload)
                st.session_state["upload_success_msg"] = "Version restored."
                st.rerun()
            except Exception as e:
                st.error(f"Error restoring version: {e}")
                return False


@st.dialog("Show PDF")
def view_pdf_dialog(
    document_name: str | None = None,
    original_name: str | None = None,
) -> None:
    """Redirect to a full page PDF view."""
    name = original_name or document_name
    if not name:
        st.error("No file found.")
        return

    if Path(name).suffix.lower() != ".pdf":
        st.info("Only PDF files can be displayed.")
        return

    st.session_state["pdf_view_name"] = name
    st.switch_page("pages/views/pdf_view.py")
