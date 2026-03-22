import pytest
from unittest.mock import patch, MagicMock
from extensions.documents.documentupload import upload_document
from extensions import pocketbase as pb
from pathlib import Path

class MockAuthStore:
    """A mock authentication store for testing purposes."""
    def __init__(self):
        self.token = ""
        self.model = None
        self.cleared = False
        self.saved = []

    def save(self, token, model):
        self.token = token
        self.model = model
        self.saved.append((token, model))

    def clear(self):
        self.token = ""
        self.model = None
        self.cleared = True


class MockCollection:
    """A mock collection to simulate PocketBase collection behavior."""
    def __init__(self, auth_with_password):
        self._auth_with_password = auth_with_password

    def auth_with_password(self, email, password):
        return self._auth_with_password(email, password)


class MockClient:
    """A mock PocketBase client for testing purposes."""
    def __init__(self, collection_obj=None):
        self.auth_store = MockAuthStore()
        self._collection_obj = collection_obj or MockCollection(
            lambda email, password: {"token": "ok"}
        )

    def collection(self, name):
        assert name == "users"
        return self._collection_obj
    
#######################################################################

class DummyCM:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

def test_upload_document_no_file_does_not_create(monkeypatch):
    import extensions.documents.documentupload as du

    upload_fn = getattr(du.upload_document, "__wrapped__", du.upload_document)

    # Streamlit mocks
    monkeypatch.setattr(du.st, "text_input", MagicMock(side_effect=["My Title", "1"]))
    monkeypatch.setattr(du.st, "multiselect", MagicMock(return_value=["id-card"]))
    monkeypatch.setattr(du.st, "file_uploader", MagicMock(return_value=None))
    monkeypatch.setattr(du.st, "button", MagicMock(return_value=True))  # egal, weil uploaded_file None
    monkeypatch.setattr(du.st, "spinner", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "error", MagicMock())
    monkeypatch.setattr(du.st, "warning", MagicMock())
    monkeypatch.setattr(du.st, "expander", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "code", MagicMock())
    monkeypatch.setattr(du.st, "rerun", MagicMock())
    du.st.session_state = {}

    # PocketBase client mock
    client = MagicMock()
    docs = MagicMock()
    client.collection.return_value = docs
    monkeypatch.setattr(du, "client", client)

    upload_fn()

    docs.create.assert_not_called()


    ######################################################

class DummyCM:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

def test_upload_document_success_creates_record_and_saves_file(monkeypatch, tmp_path):
    import extensions.documents.documentupload as du

    upload_fn = getattr(du.upload_document, "__wrapped__", du.upload_document)

    # data_dir auf tmp_path umlenken (über __file__)
    fake_mod_file = tmp_path / "extensions" / "documentupload.py"
    fake_mod_file.parent.mkdir(parents=True, exist_ok=True)
    fake_mod_file.write_text("# dummy")
    monkeypatch.setattr(du, "__file__", str(fake_mod_file), raising=False)

    # temp dir auf tmp_path/tmp umlenken
    tmp_tmp = tmp_path / "tmp"
    tmp_tmp.mkdir()
    monkeypatch.setattr(du.tempfile, "gettempdir", lambda: str(tmp_tmp))

    # Streamlit inputs
    monkeypatch.setattr(du.st, "text_input", MagicMock(side_effect=["My Doc", "1"]))
    monkeypatch.setattr(du.st, "multiselect", MagicMock(return_value=["passport"]))

    uploaded = MagicMock()
    uploaded.name = "test.pdf"
    uploaded.type = "application/pdf"
    uploaded.getvalue.return_value = b"%PDF-1.4\nhello world\n%%EOF"
    monkeypatch.setattr(du.st, "file_uploader", MagicMock(return_value=uploaded))

    # Duplicate check aus
    monkeypatch.setattr(du, "compare_with_existing_documents", MagicMock(return_value=(False, None)))

    # Button gedrückt
    monkeypatch.setattr(du.st, "button", MagicMock(return_value=True))

    # Streamlit output hooks
    monkeypatch.setattr(du.st, "spinner", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "expander", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "code", MagicMock())
    monkeypatch.setattr(du.st, "error", MagicMock())
    monkeypatch.setattr(du.st, "warning", MagicMock())
    monkeypatch.setattr(du.st, "rerun", MagicMock())
    du.st.session_state = {}

    # FileUpload mock (damit wir sauber prüfen können, dass es gebaut wird)
    fileupload = MagicMock(name="FileUpload")
    monkeypatch.setattr(du, "FileUpload", fileupload)

    # PocketBase client mock
    client = MagicMock()
    docs = MagicMock()
    client.collection.return_value = docs
    monkeypatch.setattr(du, "client", client)

    upload_fn()

    # create called?
    docs.create.assert_called_once()
    payload = docs.create.call_args.args[0]
    assert payload["title"] == "My Doc"
    assert payload["version"] == "1"
    assert payload["needed_id"] == ["passport"]
    assert payload["original_name"] == "test.pdf"

    # FileUpload gebaut?
    assert fileupload.called is True

    # Datei in data/ gespeichert?
    saved = tmp_path / "data" / "test.pdf"
    assert saved.exists()
    assert saved.read_bytes() == b"%PDF-1.4\nhello world\n%%EOF"

    # temp file weg?
    assert not (tmp_tmp / "test.pdf").exists()

    # Erfolgsmeldung gesetzt?
    assert du.st.session_state.get("upload_success_msg") == "Document uploaded successfully."

    ######################################################################

class DummyCM:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

def test_upload_document_identical_aborts(monkeypatch, tmp_path):
    import extensions.documents.documentupload as du

    upload_fn = getattr(du.upload_document, "__wrapped__", du.upload_document)

    # Streamlit inputs
    monkeypatch.setattr(du.st, "text_input", MagicMock(side_effect=["My Doc", "1"]))
    monkeypatch.setattr(du.st, "multiselect", MagicMock(return_value=["id-card"]))

    uploaded = MagicMock()
    uploaded.name = "dup.pdf"
    uploaded.type = "application/pdf"
    uploaded.getvalue.return_value = b"%PDF-1.4\nsame content\n%%EOF"
    monkeypatch.setattr(du.st, "file_uploader", MagicMock(return_value=uploaded))

    # Identisch melden
    monkeypatch.setattr(du, "compare_with_existing_documents", MagicMock(return_value=(True, None)))

    st_error = MagicMock()
    monkeypatch.setattr(du.st, "error", st_error)
    monkeypatch.setattr(du.st, "warning", MagicMock())
    monkeypatch.setattr(du.st, "expander", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "code", MagicMock())
    monkeypatch.setattr(du.st, "spinner", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "rerun", MagicMock())
    du.st.session_state = {}

    # Button "realistisch": wenn identisch, ist disabled=True – wir simulieren, dass dann nicht geklickt wird
    monkeypatch.setattr(du.st, "button", MagicMock(return_value=False))

    client = MagicMock()
    docs = MagicMock()
    client.collection.return_value = docs
    monkeypatch.setattr(du, "client", client)

    upload_fn()

    docs.create.assert_not_called()
    st_error.assert_called()  # Message check optional    

#######################################################

class DummyCM:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

def test_upload_document_similar_shows_warning_and_diff(monkeypatch, tmp_path):
    import extensions.documents.documentupload as du

    upload_fn = getattr(du.upload_document, "__wrapped__", du.upload_document)

    monkeypatch.setattr(du.st, "text_input", MagicMock(side_effect=["My Doc", "1"]))
    monkeypatch.setattr(du.st, "multiselect", MagicMock(return_value=["passport"]))

    uploaded = MagicMock()
    uploaded.name = "new.pdf"
    uploaded.type = "application/pdf"
    uploaded.getvalue.return_value = b"%PDF-1.4\nnew content\n%%EOF"
    monkeypatch.setattr(du.st, "file_uploader", MagicMock(return_value=uploaded))

    similar = (Path("existing.pdf"), 0.90, "--- diff ---")
    monkeypatch.setattr(du, "compare_with_existing_documents", MagicMock(return_value=(False, similar)))

    st_warning = MagicMock()
    st_code = MagicMock()
    monkeypatch.setattr(du.st, "warning", st_warning)
    monkeypatch.setattr(du.st, "code", st_code)
    monkeypatch.setattr(du.st, "expander", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "error", MagicMock())
    monkeypatch.setattr(du.st, "spinner", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "rerun", MagicMock())
    du.st.session_state = {}

    # Kein Upload-Klick
    monkeypatch.setattr(du.st, "button", MagicMock(return_value=False))

    client = MagicMock()
    docs = MagicMock()
    client.collection.return_value = docs
    monkeypatch.setattr(du, "client", client)

    upload_fn()

    docs.create.assert_not_called()
    st_warning.assert_called_once()
    st_code.assert_called_once()

###############################################

class DummyCM:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

def test_upload_document_requires_title(monkeypatch):
    import extensions.documents.documentupload as du

    upload_fn = getattr(du.upload_document, "__wrapped__", du.upload_document)

    # Titel nur whitespace -> title_filled False
    monkeypatch.setattr(du.st, "text_input", MagicMock(side_effect=["   ", "1"]))
    monkeypatch.setattr(du.st, "multiselect", MagicMock(return_value=["id-card"]))

    uploaded = MagicMock()
    uploaded.name = "x.pdf"
    uploaded.type = "application/pdf"
    uploaded.getvalue.return_value = b"%PDF-1.4\nx\n%%EOF"
    monkeypatch.setattr(du.st, "file_uploader", MagicMock(return_value=uploaded))

    monkeypatch.setattr(du, "compare_with_existing_documents", MagicMock(return_value=(False, None)))

    st_error = MagicMock()
    monkeypatch.setattr(du.st, "error", st_error)
    monkeypatch.setattr(du.st, "warning", MagicMock())
    monkeypatch.setattr(du.st, "expander", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "code", MagicMock())
    monkeypatch.setattr(du.st, "spinner", lambda *a, **k: DummyCM())
    monkeypatch.setattr(du.st, "rerun", MagicMock())
    du.st.session_state = {}

    # Wir “erzwingen” einen Klick – Guard im Code muss trotzdem greifen
    monkeypatch.setattr(du.st, "button", MagicMock(return_value=True))

    client = MagicMock()
    docs = MagicMock()
    client.collection.return_value = docs
    monkeypatch.setattr(du, "client", client)

    upload_fn()

    docs.create.assert_not_called()
    st_error.assert_called_once()    





# -------------------------
# show_version_list
# -------------------------

def test_show_version_list_restore_happy_path(monkeypatch, tmp_path):
    import extensions.documents.documentupload as du

    record_id = "RID"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    backup_dir = data_dir / "backup"
    backup_dir.mkdir()

    existing = data_dir / "current.pdf"
    existing.write_bytes(b"CURRENT")

    # backup file
    bfile = backup_dir / du.make_backup_name(record_id, "1", "old.pdf")
    bfile.write_bytes(b"OLDVERSION")

    # streamlit mocks
    monkeypatch.setattr(du.st, "divider", MagicMock())
    monkeypatch.setattr(du.st, "subheader", MagicMock())
    monkeypatch.setattr(du.st, "dataframe", MagicMock())
    monkeypatch.setattr(du.st, "selectbox", MagicMock(return_value=0))
    monkeypatch.setattr(du.st, "button", MagicMock(return_value=True))
    monkeypatch.setattr(du.st, "error", MagicMock())
    monkeypatch.setattr(du.st, "rerun", MagicMock())
    du.st.session_state = {}

    fu = MagicMock()
    monkeypatch.setattr(du, "FileUpload", fu)

    client = MagicMock()
    docs = MagicMock()
    client.collection.return_value = docs

    du.show_version_list(
        record_id=record_id,
        current_version="current",
        existing_path=existing,
        data_dir=data_dir,
        backup_dir=backup_dir,
        client=client,
    )

    # existing file wurde als backup gesichert
    moved = list(backup_dir.glob("RID_vcurrent_*"))
    assert len(moved) == 1

    # restored file liegt in data/
    restored = data_dir / "old.pdf"
    assert restored.exists()
    assert restored.read_bytes() == b"OLDVERSION"

    # pocketbase update
    docs.update.assert_called_once()
    payload = docs.update.call_args.args[1]
    assert payload["version"] == "1"
    assert payload["original_name"] == "old.pdf"

    assert du.st.session_state["upload_success_msg"] == "Version restored."
    du.st.rerun.assert_called_once()


def test_show_version_list_restore_update_fails_shows_error(monkeypatch, tmp_path):
    import extensions.documents.documentupload as du

    record_id = "RID"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    backup_dir = data_dir / "backup"
    backup_dir.mkdir()

    existing = data_dir / "current.pdf"
    existing.write_bytes(b"CURRENT")

    bfile = backup_dir / du.make_backup_name(record_id, "1", "old.pdf")
    bfile.write_bytes(b"OLDVERSION")

    monkeypatch.setattr(du.st, "divider", MagicMock())
    monkeypatch.setattr(du.st, "subheader", MagicMock())
    monkeypatch.setattr(du.st, "dataframe", MagicMock())
    monkeypatch.setattr(du.st, "selectbox", MagicMock(return_value=0))
    monkeypatch.setattr(du.st, "button", MagicMock(return_value=True))
    st_error = MagicMock()
    monkeypatch.setattr(du.st, "error", st_error)
    monkeypatch.setattr(du.st, "rerun", MagicMock())
    du.st.session_state = {}

    monkeypatch.setattr(du, "FileUpload", MagicMock())

    client = MagicMock()
    docs = MagicMock()
    docs.update.side_effect = RuntimeError("fail")
    client.collection.return_value = docs

    du.show_version_list(
        record_id=record_id,
        current_version="current",
        existing_path=existing,
        data_dir=data_dir,
        backup_dir=backup_dir,
        client=client,
    )

    st_error.assert_called_once()
    du.st.rerun.assert_not_called()