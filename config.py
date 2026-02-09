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
