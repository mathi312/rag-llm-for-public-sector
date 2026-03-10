import pytest
from unittest.mock import patch, MagicMock

from models import get_embeddings, get_llm, OLLAMA_BASE_URL

def test_get_embeddings_openai_missing_api_key():
    """Should raise ValueError when OpenAI provider is used without an API key."""
    with pytest.raises(ValueError, match="OpenAI API Key is required"):
        get_embeddings(
            provider="OpenAI",
            model_name="gpt-4o",
            api_key=None,
        )

def test_get_embeddings_ollama_default():
    """Should return OllamaEmbeddings when provider is not OpenAI."""
    with patch("models.OllamaEmbeddings") as mock_ollama:
        mock_instance = MagicMock()
        mock_ollama.return_value = mock_instance

        result = get_embeddings(
            provider="Local (Ollama)",
            model_name="llama3.2",
        )

        mock_ollama.assert_called_once_with(
            model="llama3.2",
            base_url=OLLAMA_BASE_URL,
        )
        assert result is mock_instance

def test_get_embeddings_with_api_key_returns_open_ai_embeddings():
    with patch("models.OpenAIEmbeddings") as mock_open_ai:
        mock_instance = MagicMock()
        mock_open_ai.return_value = mock_instance

        result = get_embeddings(
            provider="OpenAI",
            model_name="gpt-4o",
            api_key="test1234key",
        )

        mock_open_ai.assert_called_once_with(
            model='gpt-4o',
            api_key='test1234key'
        )
        assert result is mock_instance

def test_get_embeddings_unknown_provider_defaults_to_ollama():
    """Any unknown provider should default to Ollama."""
    with patch("models.OllamaEmbeddings") as mock_ollama:
        mock_instance = MagicMock()
        mock_ollama.return_value = mock_instance

        result = get_embeddings(
            provider="SomeOtherProvider",
            model_name="llama3.2",
        )

        mock_ollama.assert_called_once()
        assert result is mock_instance

def test_get_llm_openai_missing_api_key():
    """Should raise ValueError when OpenAI provider is used without an API key."""
    with pytest.raises(ValueError, match="OpenAI API Key is required"):
        get_llm(
            provider="OpenAI",
            model_name="gpt-4o",
            temperature=0.0,
            api_key=None,
        )
    
def test_get_llm_ollama_default():
    """Should return Ollama llm instance when provider is not OpenAI."""
    with patch("models.ChatOllama") as mock_ollama:
        mock_instance = MagicMock()
        mock_ollama.return_value = mock_instance

        result = get_llm(
            provider="Local (Ollama)",
            model_name="llama3.2",
            temperature=0.2,
        )

        mock_ollama.assert_called_once_with(
            model="llama3.2",
            temperature=0.2,
            base_url=OLLAMA_BASE_URL,
        )
        assert result is mock_instance


def test_get_llm_unknown_provider_defaults_to_ollama():
    """Any unknown provider should default to Ollama."""
    with patch("models.ChatOllama") as mock_ollama:
        mock_instance = MagicMock()
        mock_ollama.return_value = mock_instance

        result = get_llm(
            provider="SomeOtherProvider",
            model_name="llama3.2",
        )

        mock_ollama.assert_called_once()
        assert result is mock_instance

def test_get_llm_with_api_key_returns_open_ai_embeddings():
    with patch("models.ChatOpenAI") as mock_open_ai:
        mock_instance = MagicMock()
        mock_open_ai.return_value = mock_instance

        result = get_llm(
            provider="OpenAI",
            model_name="gpt-4o",
            api_key="test1234key",
        )

        mock_open_ai.assert_called_once_with(
            model='gpt-4o',
            temperature=0.0,
            api_key='test1234key'
        )
        assert result is mock_instance
