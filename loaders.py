"""Document loading and preprocessing module.

This module handles the ingestion of PDF and DOCX files from both
user uploads and a static local directory.
"""

import os
import tempfile
import re
from typing import List
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_core.documents import Document

from config import CHUNK_SIZE, CHUNK_OVERLAP


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
            loader = WebBaseLoader(
                url, 
                bs_kwargs=dict(
                    parse_only=None
                )
            )
            docs = loader.load()

            # normalize page content
            for doc in docs:
                doc.page_content = normalize_web_text(doc.page_content)

            documents.extend(docs)
        except Exception as e:
            print(f"Error while loading {url}: {e}")
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
    
    if not data_dir.exists():
        return documents

    print(f"Scanning {data_dir} for documents...")
    for file_path in data_dir.iterdir():
        if not file_path.is_file():
            continue
            
        try:
            filename = file_path.name.lower()
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(str(file_path))
                documents.extend(loader.load())
            elif filename.endswith(".docx"):
                loader = Docx2txtLoader(str(file_path))
                documents.extend(loader.load())
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
            
    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    """Split documents into smaller chunks for efficient embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
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