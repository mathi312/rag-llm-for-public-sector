import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from loaders import *

from langchain_core.documents import Document


class FakeUploadedFile:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


@patch("loaders.os.remove")
@patch("loaders.PyPDFLoader")
@patch("loaders.Docx2txtLoader")
def test_load_files_to_documents_pdf_and_docx(
    mock_docx_loader,
    mock_pdf_loader,
    mock_remove,
):
    pdf_doc = MagicMock()
    docx_doc = MagicMock()

    mock_pdf_loader.return_value.load.return_value = [pdf_doc]
    mock_docx_loader.return_value.load.return_value = [docx_doc]

    files = [
        FakeUploadedFile("test.pdf", b"pdf content"),
        FakeUploadedFile("test.docx", b"docx content"),
    ]

    documents = load_files_to_documents(files)

    assert documents == [pdf_doc, docx_doc]
    assert mock_remove.call_count == 2


def test_load_files_to_documents_unsupported_file():
    files = [
        FakeUploadedFile("notes.txt", b"text content"),
    ]

    documents = load_files_to_documents(files)

    assert documents == []


@patch("loaders.WebBaseLoader")
def test_load_urls_as_documents_success(mock_loader):
    doc = MagicMock()
    doc.page_content = "Hello\n\n\nWorld   ."

    mock_loader.return_value.load.return_value = [doc]

    documents = load_urls_as_documents(["https://example.com"])

    assert len(documents) == 1
    assert documents[0].page_content == "Hello\nWorld."


@patch("loaders.WebBaseLoader")
def test_load_urls_as_documents_error(mock_loader):
    mock_loader.side_effect = Exception("Load failed")

    documents = load_urls_as_documents(["https://bad-url.com"])

    assert documents == []

@patch("loaders.RecursiveCharacterTextSplitter")
def test_split_documents(mock_splitter):
    splitter_instance = MagicMock()
    splitter_instance.split_documents.return_value = ["chunk1", "chunk2"]
    mock_splitter.return_value = splitter_instance

    docs = ["doc1"]

    result = split_documents(docs)

    splitter_instance.split_documents.assert_called_once_with(docs)
    assert result == ["chunk1", "chunk2"]


def test_normalize_web_text_removes_excess_whitespace():
    text = "Hello\n\n\nWorld   .  "
    normalized = normalize_web_text(text)

    assert normalized == "Hello\nWorld."

def make_doc(text: str = "content") -> MagicMock:
    """helper function to create documents"""
    doc = MagicMock()
    doc.page_content = text
    doc.metadata = {}
    return doc


class TestLoadDirectoryDocuments:

    def test_load_directory_documents_missing_dir(self, tmp_path):
        non_existing = tmp_path / "missing"

        documents = load_directory_documents(non_existing)

        assert documents == []

    @patch("loaders.PyPDFLoader")
    @patch("loaders.Docx2txtLoader")
    def test_load_directory_documents_success(self, mock_docx, mock_pdf, tmp_path):
        pdf_file = tmp_path / "a.pdf"
        docx_file = tmp_path / "b.docx"

        pdf_file.write_text("pdf")
        docx_file.write_text("docx")

        mock_pdf.return_value.load.return_value = [
            Document(metadata={}, page_content="pdf-doc")
        ]
        mock_docx.return_value.load.return_value = [
            Document(metadata={}, page_content="docx-doc")
        ]

        documents = load_directory_documents(tmp_path)

        assert len(documents) == 2

        by_source = {doc.metadata["source"]: doc for doc in documents}

        assert str(pdf_file) in by_source
        assert str(docx_file) in by_source

        assert by_source[str(pdf_file)].page_content == "pdf-doc"
        assert by_source[str(pdf_file)].metadata["needed_id"] == []

        assert by_source[str(docx_file)].page_content == "docx-doc"
        assert by_source[str(docx_file)].metadata["needed_id"] == []

    def test_pdf_loader_is_used(self, tmp_path):
        (tmp_path / "report.pdf").write_bytes(b"%PDF fake")
        fake_doc = make_doc()

        with patch("extensions.documents.documentupload.list_documents", return_value=[]), \
             patch("loaders.PyPDFLoader") as MockLoader:

            MockLoader.return_value.load.return_value = [fake_doc]
            result = load_directory_documents(tmp_path)

        MockLoader.assert_called_once()
        assert len(result) == 1

    def test_docx_loader_is_used(self, tmp_path):
        (tmp_path / "contract.docx").write_bytes(b"PK fake docx")
        fake_doc = make_doc()

        with patch("extensions.documents.documentupload.list_documents", return_value=[]), \
             patch("loaders.Docx2txtLoader") as MockLoader:

            MockLoader.return_value.load.return_value = [fake_doc]
            result = load_directory_documents(tmp_path)

        MockLoader.assert_called_once()
        assert len(result) == 1

    def test_only_supported_files_are_loaded(self, tmp_path):
        (tmp_path / "a.pdf").write_bytes(b"%PDF fake")
        (tmp_path / "b.docx").write_bytes(b"PK fake")
        (tmp_path / "c.txt").write_text("ignored")
        (tmp_path / "d.jpg").write_bytes(b"jpg")

        pdf_doc = make_doc("from pdf")
        docx_doc = make_doc("from docx")

        with patch("extensions.documents.documentupload.list_documents", return_value=[]), \
            patch("loaders.PyPDFLoader") as MockPDF, \
            patch("loaders.Docx2txtLoader") as MockDOCX:

            MockPDF.return_value.load.return_value = [pdf_doc]
            MockDOCX.return_value.load.return_value = [docx_doc]
            result = load_directory_documents(tmp_path)

        assert len(result) == 2
        assert pdf_doc in result
        assert docx_doc in result

    def test_ignores_txt_and_csv(self, tmp_path):
        (tmp_path / "readme.txt").write_text("ignored")
        (tmp_path / "data.csv").write_text("ignored")

        with patch("extensions.documents.documentupload.list_documents", return_value=[]):
            result = load_directory_documents(tmp_path)

        assert result == []

    def test_exception_during_loader_construction_skips_file(self, tmp_path):
        (tmp_path / "doc.pdf").write_bytes(b"%PDF fake")

        with patch("extensions.documents.documentupload.list_documents", return_value=[]), \
             patch("loaders.PyPDFLoader", side_effect=Exception("init error")):

            result = load_directory_documents(tmp_path)

        assert result == []

    def test_ignores_subdirectories(self, tmp_path):
        (tmp_path / "subdir").mkdir()

        with patch("extensions.documents.documentupload.list_documents", return_value=[]):
            result = load_directory_documents(tmp_path)

        assert result == []


class TestNeededIdMetadata:

    def _load(self, tmp_path, records, filename="doc.pdf"):
        f = tmp_path / filename
        f.write_bytes(b"%PDF fake" if filename.endswith(".pdf") else b"PK fake")
        fake_doc = make_doc()
        loader_patch = "loaders.PyPDFLoader" if filename.endswith(".pdf") \
                       else "loaders.Docx2txtLoader"

        with patch("extensions.documents.documentupload.list_documents", return_value=records), \
             patch(loader_patch) as MockLoader:

            MockLoader.return_value.load.return_value = [fake_doc]
            load_directory_documents(tmp_path)

        return fake_doc

    def test_needed_id_set_via_original_name(self, tmp_path):
        records = [{"original_name": "doc.pdf", "document_name": None, "needed_id": ["passport"]}]
        doc = self._load(tmp_path, records, "doc.pdf")
        assert doc.metadata["needed_id"] == ["passport"]

    def test_needed_id_set_via_document(self, tmp_path):
        records = [{"original_name": None, "document": "doc.pdf", "needed_id": ["id_card"]}]
        doc = self._load(tmp_path, records, "doc.pdf")
        assert doc.metadata["needed_id"] == ["id_card"]

    def test_needed_id_set_via_legacy_document_name(self, tmp_path):
        records = [{"original_name": None, "document_name": "doc.pdf", "needed_id": ["id_card"]}]
        doc = self._load(tmp_path, records, "doc.pdf")
        assert doc.metadata["needed_id"] == ["id_card"]

    def test_needed_id_empty_when_no_match(self, tmp_path):
        records = [{"original_name": "other.pdf", "document_name": None, "needed_id": ["passport"]}]
        doc = self._load(tmp_path, records, "doc.pdf")
        assert doc.metadata["needed_id"] == []

    def test_needed_id_empty_when_record_list_is_empty(self, tmp_path):
        doc = self._load(tmp_path, [], "doc.pdf")
        assert doc.metadata["needed_id"] == []

    def test_needed_id_with_multiple_values(self, tmp_path):
        records = [{"original_name": "doc.pdf", "document_name": None,
                    "needed_id": ["passport", "driving_license", "id_card"]}]
        doc = self._load(tmp_path, records, "doc.pdf")
        assert doc.metadata["needed_id"] == ["passport", "driving_license", "id_card"]


class TestListDocumentsFallback:

    def test_exception_in_list_documents_falls_back_to_empty_map(self, tmp_path):
        (tmp_path / "doc.pdf").write_bytes(b"%PDF fake")
        fake_doc = make_doc()

        with patch("extensions.documents.documentupload.list_documents", side_effect=RuntimeError("DB down")), \
             patch("loaders.PyPDFLoader") as MockLoader:

            MockLoader.return_value.load.return_value = [fake_doc]
            result = load_directory_documents(tmp_path)

        assert fake_doc in result
        assert fake_doc.metadata["needed_id"] == []

    def test_docs_still_loaded_when_list_documents_fails(self, tmp_path):
        (tmp_path / "doc.pdf").write_bytes(b"%PDF fake")
        fake_doc = make_doc()

        with patch("extensions.documents.documentupload.list_documents", side_effect=Exception("any error")), \
             patch("loaders.PyPDFLoader") as MockLoader:

            MockLoader.return_value.load.return_value = [fake_doc]
            result = load_directory_documents(tmp_path)

        assert len(result) == 1
