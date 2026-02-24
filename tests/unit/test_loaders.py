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


def test_load_directory_documents_missing_dir(tmp_path):
    non_existing = tmp_path / "missing"

    documents = load_directory_documents(non_existing)

    assert documents == []


@patch("loaders.PyPDFLoader")
@patch("loaders.Docx2txtLoader")
def test_load_directory_documents_success(mock_docx, mock_pdf, tmp_path):
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
