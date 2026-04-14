"""Document loading and preprocessing module.

This module handles the ingestion of PDF and DOCX files from both
user uploads and a static local directory.
"""

import os
import tempfile
import re
from typing import List
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    WebBaseLoader,
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain_core.documents import Document

from config import CHUNK_SIZE, CHUNK_OVERLAP

from application.logger import Logger

logger = Logger()

def load_files_to_documents(uploaded_files) -> List[Document]:
    """Convert uploaded Streamlit file objects into LangChain Documents.

    Args:
        uploaded_files: List of Streamlit UploadedFile objects.

    Returns:
        List[Document]: Parsed documents.
    """
    documents: List[Document] = []

    for file in uploaded_files:
        suffix = f".{file.name.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name

        try:
            filename = file.name.lower()
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(tmp_path)
            elif filename.endswith(".docx"):
                loader = Docx2txtLoader(tmp_path)
            else:
                continue
            documents.extend(loader.load())
        finally:
            os.remove(tmp_path)

    return documents


def load_urls_as_documents(urls) -> List[Document]:
    """Load the content of the given urls.

    Args:
        urls: List of urls.

    Returns:
        List[Document]: List of loaded documents from the urls.
    """
    documents: List[Document] = []

    for url in urls:
        try:
            loader = WebBaseLoader(url, bs_kwargs=dict(parse_only=None))
            docs = loader.load()

            # normalize page content
            for doc in docs:
                doc.page_content = normalize_web_text(doc.page_content)

            documents.extend(docs)
        except Exception as e:
            logger.log_error(f"Error while loading {url}: {str(e)}")
            continue

    return documents


def load_directory_documents(data_dir: Path) -> List[Document]:
    """Load all PDF/DOCX files from a specific directory path.

    Args:
        data_dir: Path object pointing to the directory containing documents.

    Returns:
        List[Document]: List of loaded documents from the directory.
    """
    documents: List[Document] = []
    needed_id_map: dict[str, list[str]] = {}

    if not data_dir.exists():
        return documents

    # Mapping: filename -> required IDs
    try:
        from application.documents.documentupload import list_documents

        for rec in list_documents():
            ids = rec.get("needed_id") or []
            original_name = rec.get("original_name")
            document_name = rec.get("document")
            legacy_document_name = rec.get("document_name")

            if original_name:
                needed_id_map[original_name] = ids
            if document_name:
                needed_id_map[document_name] = ids
            elif legacy_document_name:
                needed_id_map[legacy_document_name] = ids
    except Exception:
        needed_id_map = {}

    logger.log_info(f"Scanning {data_dir} for documents...")
    for file_path in data_dir.iterdir():
        if not file_path.is_file():
            continue

        try:
            filename = file_path.name.lower()
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(str(file_path))
            elif filename.endswith(".docx"):
                loader = Docx2txtLoader(str(file_path))
            else:
                continue
        except Exception as e:
            logger.log_info(f"Error loading {file_path}: {str(e)}")
            continue
        
        # Load the document and attach metadata about source and needed IDs.
        docs = loader.load()

        for doc in docs:
            doc.metadata["source"] = str(file_path)
            doc.metadata["needed_id"] = needed_id_map.get(file_path.name, [])
        documents.extend(docs)

    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    """Split documents into smaller chunks for efficient embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(documents)


def normalize_web_text(text: str) -> str:
    """Normalize the text of a webpage."""
    # Remove excessive newlines
    text = re.sub(r"\n{2,}", "\n", text)
    # Remove excessive spaces
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Fix broken punctuation spacing
    text = re.sub(r"\s+\.", ".", text)

    return text.strip()
