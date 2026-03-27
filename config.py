"""Configuration module for the RAG application.

This module defines application-wide constants and paths used throughout
the system, including the directory for persisting FAISS vector stores
and text chunking parameters.
"""

from pathlib import Path

# Base directory is resolved relative to this configuration file's location.
BASE_DIR = Path(__file__).resolve().parent

# Directory where the FAISS vector index is persisted to disk.
INDEX_DIR = BASE_DIR / "faiss_index"

# Maximum number of characters per text chunk when splitting documents.
CHUNK_SIZE = 1000

# Number of overlapping characters between consecutive chunks.
CHUNK_OVERLAP = 200

# Directory for storing log files.
LOG_DIR = BASE_DIR / "logs"

# RAG pipeline configuration constants, including system prompt and retrieval parameters.
NO_CONTEXT_ANSWER = "Ich kann auf Basis der bereitgestellten Quellen keine Antwort geben."
RETRIEVAL_K = 24
GATE_MIN_SCORE = 0.12
GATE_RELATIVE_FACTOR = 0.55
GATE_MAX_DOCS = 8
GATE_MAX_DOCS_PER_SOURCE = 2

SYSTEM_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If the answer is not in the context, answer exactly with"
    f'"{NO_CONTEXT_ANSWER}". '
    "Do not use any external knowledge and don't make assumptions. "
    "Keep the answer concise.\n\n{context}"
)

DOCUMENT_KEYWORDS = [
    "führungszeugnis",
    "dokument",
    "bescheinigung",
    "auszug",
    "urkunde",
]