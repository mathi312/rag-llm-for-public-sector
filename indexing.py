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


def load_index(embeddings: Embeddings) -> Optional[FAISS]:
    """Attempt to load a persisted FAISS index from the configured directory."""
    if not INDEX_DIR.exists():
        print(f"Index directory {INDEX_DIR} does not exist.")
        return None
    
    try:
        print(f"Loading index from {INDEX_DIR}...")
        vector_store = FAISS.load_local(
            INDEX_DIR.as_posix(),
            embeddings,
            allow_dangerous_deserialization=True
        )
        print("Index loaded successfully.")
        return vector_store
    except Exception as e:
        print(f"Failed to load index: {e}")
        return None


def build_index_from_documents(
    documents: List[Document],
    embeddings: Embeddings,
    batch_size: int = 32
) -> FAISS:
    """Create a new FAISS vector index from document chunks and persist it.
    
    Uses batching to avoid 'signal: killed' (OOM) errors.
    """
    print(f"Starting to embed {len(documents)} document chunks with batch size {batch_size}...")
    start_time = time.time()

    vector_store = None
    total_docs = len(documents)

    # Process in batches
    for i in range(0, total_docs, batch_size):
        batch = documents[i : i + batch_size]
        print(f"Processing batch {i + 1} to {min(i + batch_size, total_docs)}...")
        
        if vector_store is None:
            vector_store = FAISS.from_documents(batch, embeddings)
        else:
            vector_store.add_documents(batch)

    duration = time.time() - start_time
    print(f"Embedding finished in {duration:.2f} seconds.")

    # Save to disk
    if vector_store:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(INDEX_DIR.as_posix())
        print(f"Index saved to {INDEX_DIR}")
    
    return vector_store
