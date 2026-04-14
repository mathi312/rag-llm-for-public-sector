"""Vector store indexing and persistence module.

This module manages the lifecycle of the FAISS vector index, including
loading existing indexes and building new ones with batch processing
to manage memory usage.
"""

import time
from typing import Optional, List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config import INDEX_DIR

from application.logger import Logger
from domain.indexing.excpetions import (
    IndexDoesntExistError,
    IndexLoadError,
    IndexBuildError
)

logger = Logger()

def load_index(embeddings: Embeddings) -> Optional[FAISS]:
    """Attempt to load a persisted FAISS index from the configured directory."""
    if not INDEX_DIR.exists():
        msg =  f"Index directory {INDEX_DIR} does not exist. Please build the index first."
        logger.log_warning(msg)
        raise IndexDoesntExistError(msg)

    try:
        logger.log_info(f"Loading index from {INDEX_DIR}...")

        vector_store = FAISS.load_local(
            INDEX_DIR.as_posix(),
            embeddings,
            allow_dangerous_deserialization=True
        )

        logger.log_info("Index loaded successfully.")

        return vector_store
    except Exception as e:
        logger.log_error(f"Failed to load index: {str(e)}")
        raise IndexLoadError(f"Failed to load index from {INDEX_DIR}") from e



def build_index_from_documents(
    documents: List[Document],
    embeddings: Embeddings,
    batch_size: int = 32
) -> FAISS:
    """Create a new FAISS vector index from document chunks and persist it.
    
    Uses batching to avoid 'signal: killed' (OOM) errors.
    """
    logger.log_info(
        f"Starting to embed {len(documents)} document chunks with batch size {batch_size}..."
    )
    start_time = time.time()

    vector_store = None
    total_docs = len(documents)

    try:
        # Process in batches
        for i in range(0, total_docs, batch_size):
            batch = documents[i : i + batch_size]
            logger.log_info(f"Processing batch {i + 1} to {min(i + batch_size, total_docs)}...")

            if vector_store is None:
                vector_store = FAISS.from_documents(batch, embeddings)
            else:
                vector_store.add_documents(batch)

        duration = time.time() - start_time

        logger.log_info(f"Embedding finished in {duration:.2f} seconds.")

        # Save to disk
        if vector_store:
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            vector_store.save_local(INDEX_DIR.as_posix())
            logger.log_info(f"Index saved to {INDEX_DIR}")

        return vector_store
    except Exception as e:
        logger.log_error(f"Failed to build index from documents: {str(e)}")
        raise IndexBuildError(f"Failed to build index: {str(e)}") from e
