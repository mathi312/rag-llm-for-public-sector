import pytest
from typing import Optional, List
from unittest.mock import MagicMock, patch, call
from pathlib import Path

from langchain_core.documents import Document

from application.indexing import load_index, build_index_from_documents


class TestLoadIndex:
    """Tests for loading persisted FAISS indexes"""
    
    @patch("application.indexing.FAISS.load_local")
    @patch("application.indexing.INDEX_DIR")
    def test_load_index_success(self, mock_index_dir, mock_load_local):
        """Test successful loading of an existing index"""
        mock_index_dir.exists.return_value = True
        mock_vector_store = MagicMock()
        mock_load_local.return_value = mock_vector_store
        mock_embeddings = MagicMock()
        
        result = load_index(mock_embeddings)
        
        assert result == mock_vector_store
        mock_index_dir.exists.assert_called_once()
        mock_load_local.assert_called_once_with(
            mock_index_dir.as_posix.return_value,
            mock_embeddings,
            allow_dangerous_deserialization=True
        )
    
    @patch("application.indexing.INDEX_DIR")
    def test_load_index_directory_not_exists(self, mock_index_dir):
        """Test when index directory doesn't exist"""
        mock_index_dir.exists.return_value = False
        mock_embeddings = MagicMock()
        
        result = load_index(mock_embeddings)
        
        assert result is None
        mock_index_dir.exists.assert_called_once()
    
    @patch("application.indexing.FAISS.load_local")
    @patch("application.indexing.INDEX_DIR")
    def test_load_index_exception(self, mock_index_dir, mock_load_local):
        """Test error handling when loading fails"""
        mock_index_dir.exists.return_value = True
        mock_load_local.side_effect = Exception("Load failed")
        mock_embeddings = MagicMock()
        
        result = load_index(mock_embeddings)
        
        assert result is None
        mock_load_local.assert_called_once()


class TestBuildIndexFromDocuments:
    INDEX_DIR_PATH = Path("/tmp/faiss_test_index")

    def make_docs(self, n: int) -> List[Document]:
        return [Document(page_content=f"chunk {i}") for i in range(n)]

    def setup_vector_store_mock(self):
        store = MagicMock(name="vector_store_0")
        faiss_cls = faiss_cls = MagicMock(name="FAISS")
        faiss_cls.from_documents.return_value = store
        return faiss_cls, store

    def test_load_index_success(self):
        embeddings = MagicMock(name="Embeddings")
        docs = self.make_docs(5)

        faiss_cls, store = self.setup_vector_store_mock()

        with patch("application.indexing.FAISS", faiss_cls):
            result = build_index_from_documents(docs, embeddings, batch_size=32)

        assert result is store

    def test_returns_none_for_empty_document_list(self):
        embeddings = MagicMock(name="Embeddings")

        result = build_index_from_documents([], embeddings, batch_size=32)
        assert result is None

    def test_two_batches(self):
        """6 docs, batch_size=4 → first batch via from_documents, second via add_documents."""
        embeddings = MagicMock(name="Embeddings")
        docs = self.make_docs(6)

        faiss_cls, store = self.setup_vector_store_mock()

        with patch("application.indexing.FAISS", faiss_cls):
            build_index_from_documents(docs, embeddings, batch_size=4)

        faiss_cls.from_documents.assert_called_once_with(docs[:4], embeddings)
        store.add_documents.assert_called_once_with(docs[4:])

    def test_save_local_called_with_index_dir(self):
        embeddings = MagicMock(name="Embeddings")
        docs = self.make_docs(3)
        faiss_cls, store = self.setup_vector_store_mock()

        with patch("application.indexing.FAISS", faiss_cls), \
            patch("application.indexing.INDEX_DIR", self.INDEX_DIR_PATH):
            build_index_from_documents(docs, embeddings, batch_size=32)

        store.save_local.assert_called_once_with(self.INDEX_DIR_PATH.as_posix())

    def test_save_local_not_called_for_empty_documents(self):
        embeddings = MagicMock(name="Embeddings")
        faiss_cls, store = self.setup_vector_store_mock()

        with patch("application.indexing.FAISS", faiss_cls):
            build_index_from_documents([], embeddings, batch_size=32)

        store.save_local.assert_not_called()
