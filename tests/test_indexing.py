import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

from indexing import load_index, build_index_from_documents


class TestLoadIndex:
    """Tests for loading persisted FAISS indexes"""
    
    @patch("indexing.FAISS.load_local")
    @patch("indexing.INDEX_DIR")
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
    
    @patch("indexing.INDEX_DIR")
    def test_load_index_directory_not_exists(self, mock_index_dir):
        """Test when index directory doesn't exist"""
        mock_index_dir.exists.return_value = False
        mock_embeddings = MagicMock()
        
        result = load_index(mock_embeddings)
        
        assert result is None
        mock_index_dir.exists.assert_called_once()
    
    @patch("indexing.FAISS.load_local")
    @patch("indexing.INDEX_DIR")
    def test_load_index_exception(self, mock_index_dir, mock_load_local):
        """Test error handling when loading fails"""
        mock_index_dir.exists.return_value = True
        mock_load_local.side_effect = Exception("Load failed")
        mock_embeddings = MagicMock()
        
        result = load_index(mock_embeddings)
        
        assert result is None
        mock_load_local.assert_called_once()
