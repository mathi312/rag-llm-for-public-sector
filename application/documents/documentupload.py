import os
import tempfile
import mimetypes
import io
import zipfile
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
import hashlib
from application.documents import DocumentController, build_document_controller
from application.logger import Logger
from domain.auth.pocketbase_messages import PBLog
from infrastructure.pocketbase import get_pocketbase_client
from config import BASE_DIR

pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
client = get_pocketbase_client()
logger = Logger()

ALLOWED_DOCUMENT_SUFFIXES = {".pdf", ".docx"}
ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}


def _session_authenticated_client() -> PocketBase:
    """Return a client authenticated with current session token if available."""
    auth_data = st.session_state.get("pb_auth")
    if not isinstance(auth_data, dict):
        return client

    token = auth_data.get("token")
    model = auth_data.get("model")
    if not token or model is None:
        return client

    scoped_client = PocketBase(pb_url)
    auth_store = getattr(scoped_client, "auth_store", None)
    if auth_store is None or not hasattr(auth_store, "save"):
        return client

    try:
        auth_store.save(token, model)
        return scoped_client
    except Exception as exc:
        logger.log_warning(PBLog.RESTORE_AUTH_FROM_STORE_FAILED.value.format(error=exc))
        return client


def _document_controller() -> DocumentController:
    data_dir = BASE_DIR / "data"
    return build_document_controller(_session_authenticated_client(), data_dir)


def _is_pdf_bytes(content: bytes) -> bool:
    return content.startswith(b"%PDF-")


def _is_docx_bytes(content: bytes) -> bool:
    # DOCX files are ZIP archives and should contain typical OOXML entries.
    if not content.startswith(b"PK"):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as zf:
            names = set(zf.namelist())
            return "[Content_Types].xml" in names and any(
                name.startswith("word/") for name in names
            )
    except Exception:
        return False


def validate_document_upload(name: str, mime_type: str | None, content: bytes) -> tuple[bool, str | None]:
    suffix = Path(name or "").suffix.lower()
    if suffix not in ALLOWED_DOCUMENT_SUFFIXES:
        return False, "Only PDF and DOCX files are allowed."

    normalized_mime = (mime_type or "application/octet-stream").lower()
    if normalized_mime not in ALLOWED_DOCUMENT_MIME_TYPES:
        return False, "Invalid file type. Please upload a valid PDF or DOCX file."

    if suffix == ".pdf" and not _is_pdf_bytes(content):
        return False, "Invalid PDF file signature."

    if suffix == ".docx" and not _is_docx_bytes(content):
        return False, "Invalid DOCX file signature."

    return True, None


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
    is_valid_upload = True
    file_bytes = None

    # Check for identical or similar documents before allowing upload, to prevent duplicates and provide user feedback on potential matches.
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        is_valid_upload, validation_error = validate_document_upload(
            uploaded_file.name,
            uploaded_file.type,
            file_bytes,
        )
        if not is_valid_upload:
            st.error(validation_error or "Invalid file.")
        else:
            document_controller = _document_controller()
            temp_file_path = document_controller.create_temp_copy(uploaded_file.name, file_bytes)

            try:
                is_identical, similar = compare_with_existing_documents(
                    temp_file_path, document_controller.data_dir, similarity_threshold=0.85
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
        st.button(
            "Upload",
            disabled=identical or not uploaded_file or not title_filled or not is_valid_upload,
        )
        and uploaded_file
    ):
        if not title_filled:
            st.error("Bitte einen Titel eingeben.")
            return None
        if not is_valid_upload:
            st.error("Only valid PDF and DOCX files are allowed.")
            return None
        with st.spinner("Uploading document..."):
            document_controller = _document_controller()
            temp_file_path = document_controller.create_temp_copy(
                uploaded_file.name,
                uploaded_file.getvalue(),
            )
            try:
                document_controller.create_record(
                    title=title,
                    version=version,
                    needed_id=needed_id,
                    original_name=uploaded_file.name,
                    local_path=str(temp_file_path),
                    mime_type=uploaded_file.type or "application/octet-stream",
                    file_upload=FileUpload(
                        (
                            str(temp_file_path),
                            uploaded_file.name,
                            uploaded_file.type or "application/octet-stream",
                        )
                    ),
                )

                document_controller.save_to_data_dir(temp_file_path, uploaded_file.name)

                st.session_state["upload_success_msg"] = (
                    "Document uploaded successfully."
                )
                st.rerun()
            except Exception as e:
                logger.log_error(f"Failed to upload document '{uploaded_file.name}': {e}")
                st.error(f"Failed to upload document: {e}")
            finally:
                if temp_file_path.exists():
                    temp_file_path.unlink()
    return None


def list_documents() -> list[dict]:
    """List all documents from PocketBase, sorted by most recently updated first."""
    try:
        records = _document_controller().list_records()
        docs = [
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
        # Sort by updated timestamp (newest first)
        docs.sort(key=lambda x: x.get("updated") or x.get("created") or "", reverse=True)
        return docs
    except Exception as e:
        logger.log_error(f"Failed to fetch documents list: {e}")
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
            ok = delete_document(record_id=record_id)
            if ok:
                st.session_state["upload_success_msg"] = "Document deleted."
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    return False


def delete_document(record_id: str) -> bool:
    """Delete a document record and remove all associated files (data and backups).
    
    Uses record_id to find and delete:
    - Main document file from data/
    - All backup versions from data/backup/ (regardless of filename changes over time)
    """
    document_controller = _document_controller()
    original_name = None
    
    # First, retrieve the record to get the original filename
    try:
        records = document_controller.list_records()
        for record in records:
            if record.id == record_id:
                original_name = getattr(record, "original_name", None)
                break
    except Exception as e:
        logger.log_warning(f"Could not retrieve original filename for record '{record_id}': {e}")
    
    # Delete the PocketBase record
    processed = False
    try:
        document_controller.delete_record(record_id)
        processed = True
    except Exception as e:
        logger.log_error(f"Failed to delete document record '{record_id}': {e}")
        st.error(f"Failed to delete document: {e}")
    
    # Delete the main file from data_dir (if we know its name)
    if original_name:
        try:
            document_controller.delete_from_data_dir({original_name})
        except Exception as e:
            logger.log_warning(f"Could not delete main document file for record '{record_id}': {e}")
    
    # Delete all backups for this document (search by record_id prefix)
    try:
        backup_dir = document_controller.backup_dir
        
        if backup_dir and backup_dir.exists():
            # Find and delete all backups that start with {record_id}_v
            # This works regardless of how many times the file was renamed
            for backup_file in backup_dir.iterdir():
                if backup_file.is_file() and backup_file.name.startswith(f"{record_id}_v"):
                    backup_file.unlink()
                    logger.log_info(f"Deleted backup: {backup_file.name}")
    except Exception as e:
        logger.log_error(f"Could not delete backup files for record '{record_id}': {e}")
        st.error(f"Could not delete backup files: {e}")
    
    return processed


def extract_text_from_file(file_path: Path) -> str:
    """Extract text content from a pdf or docx file."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        try:
            reader = PdfReader(str(file_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            logger.log_warning(f"Could not read PDF '{file_path}': {exc}")
            try:
                return file_path.read_bytes().decode("utf-8", errors="ignore")
            except Exception:
                return ""
    if suffix == ".docx":
        try:
            return docx2txt.process(str(file_path)) or ""
        except Exception as exc:
            logger.log_warning(f"Could not read DOCX '{file_path}': {exc}")
            try:
                return file_path.read_bytes().decode("utf-8", errors="ignore")
            except Exception:
                return ""
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


def build_binary_diff(old_path: Path, new_path: Path) -> str:
    """Build a compact binary diff summary when textual extraction is unavailable."""
    old_bytes = old_path.read_bytes()
    new_bytes = new_path.read_bytes()

    old_hash = hashlib.sha256(old_bytes).hexdigest()[:12]
    new_hash = hashlib.sha256(new_bytes).hexdigest()[:12]

    return "\n".join(
        [
            f"--- ALT(bin): {old_path.name}",
            f"+++ NEU(bin): {new_path.name}",
            "@@ Binary comparison @@",
            f"- size: {len(old_bytes)} bytes, sha256: {old_hash}",
            f"+ size: {len(new_bytes)} bytes, sha256: {new_hash}",
            "! No extractable text found; showing binary-level comparison.",
        ]
    )


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
    return _document_controller().backup_dir


def make_backup_name(record_id: str, version: str, original_name: str) -> str:
    """Create a backup filename based on record ID, version, and original name."""
    safe_version = str(version).strip().replace(" ", "_")
    return f"{record_id}_v{safe_version}_{original_name}"


def find_current_document_version(
    record_id: str,
    current_version: str,
    existing_name: str,
    data_dir: Path,
    backup_dir: Path,
) -> Path | None:
    """
    Find the current version of a document.
    First check data_dir, then check backup_dir for the current version.
    If not found, search for ANY backup with the matching filename (most recent).
    Returns the Path if found, None otherwise.
    """
    if not existing_name:
        return None

    # Check data_dir first
    data_path = data_dir / existing_name
    if data_path.exists():
        return data_path

    # Check backup_dir for the exact record_id + current version
    backup_pattern = make_backup_name(record_id, current_version or "current", existing_name)
    backup_path = backup_dir / backup_pattern
    if backup_path.exists():
        return backup_path

    # Fallback: Search for ANY backup with the matching filename (most recent by mtime)
    if backup_dir.exists():
        matching_backups = []
        for p in backup_dir.iterdir():
            if p.is_file() and p.name.endswith(existing_name):
                matching_backups.append(p)
        
        if matching_backups:
            # Return the most recently modified one
            return max(matching_backups, key=lambda p: p.stat().st_mtime)

    return None


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

    uploaded_bytes = None
    is_valid_upload = True
    if uploaded_file:
        uploaded_bytes = uploaded_file.getvalue()
        is_valid_upload, validation_error = validate_document_upload(
            uploaded_file.name,
            uploaded_file.type,
            uploaded_bytes,
        )
        if not is_valid_upload:
            st.error(validation_error or "Invalid file.")

    document_controller = _document_controller()
    data_dir = document_controller.data_dir
    backup_dir = document_controller.backup_dir

    # Determine existing file path for diffing
    existing_name = original_name or document_name
    existing_path = find_current_document_version(
        record_id, current_version, existing_name, data_dir, backup_dir
    )

    diff_text = ""
    identical = False
    if uploaded_file and is_valid_upload and existing_path and existing_path.exists():
        temp_compare_path = document_controller.create_temp_copy(
            uploaded_file.name,
            uploaded_bytes or b"",
        )

        old_text = extract_text_from_file(existing_path)
        new_text = extract_text_from_file(temp_compare_path)
        old_text_clean = old_text.strip()
        new_text_clean = new_text.strip()
        if old_text_clean or new_text_clean:
            identical = old_text_clean == new_text_clean
        else:
            identical = existing_path.read_bytes() == temp_compare_path.read_bytes()

        if not identical and (old_text_clean or new_text_clean):
            diff_text = build_diff(
                old_text,
                new_text,
                fromfile=f"ALT: {existing_path.name}",
                tofile=f"NEU: {uploaded_file.name}",
            )
        elif not identical:
            diff_text = build_binary_diff(existing_path, temp_compare_path)

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
        disabled=identical or not uploaded_file or not is_valid_upload,
    )

    show_version_list(
        record_id=record_id,
        current_version=current_version or "current",
        existing_path=existing_path,
        data_dir=data_dir,
        backup_dir=backup_dir,
        document_controller=document_controller,
    )

    ids_changed = set(needed_id or []) != set(orig_needed_id or [])
    title_changed = title != orig_title
    changed = title_changed or ids_changed or bool(uploaded_file)

    if not changed:
        st.info("No changes detected. Update is disabled.")

    update_disabled = (
        (not changed)
        or bool(uploaded_file and identical)
        or bool(uploaded_file and not is_valid_upload)
        or (bool(uploaded_file) and not confirm_update)
    )

    if st.button("Update", disabled=update_disabled):
        if uploaded_file and (identical or not confirm_update):
            st.warning(
                "Update aborted. Your document is identical in content or changes were not confirmed."
            )
            return False
        if uploaded_file and not is_valid_upload:
            st.warning("Update aborted. Only valid PDF and DOCX files are allowed.")
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
                temp_file_path = document_controller.create_temp_copy(
                    uploaded_file.name,
                    uploaded_bytes or b"",
                )
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

            # Move old file to backup ONLY if a new file is being uploaded
            if uploaded_file:
                old_name = original_name or document_name
                if old_name:
                    backup_name = make_backup_name(
                        record_id, current_version or "current", old_name
                    )
                    document_controller.move_to_backup(old_name, backup_name)

            document_controller.update_record(record_id, payload)

            # save new file to data/ if it was uploaded
            if local_path and local_path.exists():
                document_controller.save_to_data_dir(local_path, fname)

            st.session_state["upload_success_msg"] = "Document updated."
            st.rerun()
        except Exception as e:
            logger.log_error(f"Failed to update document '{record_id}': {e}")
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
    document_controller: DocumentController | None = None,
    client=None,
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
                if document_controller is not None:
                    document_controller.update_record(record_id, payload)
                elif client is not None:
                    client.collection("documents").update(record_id, payload)
                else:
                    raise ValueError(
                        "Either document_controller or client must be provided."
                    )
                st.session_state["upload_success_msg"] = "Version restored."
                st.rerun()
            except Exception as e:
                logger.log_error(f"Error restoring document version for '{record_id}': {e}")
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
    st.switch_page("presentation/views/pdf_view.py")
