import pytest
from unittest.mock import MagicMock, call, patch

from extensions.models.models import get_embeddings, get_llm, ModelConfig


def _assert_model_config(mock_factory_method, **expected_fields):
    """Assert the factory was called once and the ModelConfig matches expectations."""
    mock_factory_method.assert_called_once()
    actual_config: ModelConfig = mock_factory_method.call_args.kwargs["config"]
    assert isinstance(actual_config, ModelConfig)
    for field, value in expected_fields.items():
        assert getattr(actual_config, field) == value, (
            f"ModelConfig.{field}: expected {value!r}, got {getattr(actual_config, field)!r}"
        )


class TestGetEmbeddings:
    @patch("extensions.models.models.embeddings_factory")
    def test_returns_result_from_factory(self, mock_factory):
        expected = MagicMock()
        mock_factory.create_embeddings.return_value = expected

        result = get_embeddings(provider="OpenAI", model_name="text-embedding-3-small", api_key="sk-abc")

        assert result is expected

    @patch("extensions.models.models.embeddings_factory")
    def test_passes_correct_config_to_factory(self, mock_factory):
        get_embeddings(provider="OpenAI", model_name="text-embedding-3-small", api_key="sk-abc")

        _assert_model_config(
            mock_factory.create_embeddings,
            provider="OpenAI",
            model_name="text-embedding-3-small",
            api_key="sk-abc",
        )

    @patch("extensions.models.models.embeddings_factory")
    def test_api_key_defaults_to_none(self, mock_factory):
        get_embeddings(provider="Local (Ollama)", model_name="llama3.2")

        _assert_model_config(
            mock_factory.create_embeddings,
            provider="Local (Ollama)",
            model_name="llama3.2",
            api_key=None,
        )

    @patch("extensions.models.models.embeddings_factory")
    def test_factory_called_exactly_once(self, mock_factory):
        get_embeddings(provider="OpenAI", model_name="text-embedding-3-small", api_key="sk-abc")

        mock_factory.create_embeddings.assert_called_once()

    @patch("extensions.models.models.embeddings_factory")
    def test_propagates_factory_exception(self, mock_factory):
        mock_factory.create_embeddings.side_effect = NotImplementedError("Unsupported")

        with pytest.raises(NotImplementedError, match="Unsupported"):
            get_embeddings(provider="unknown", model_name="some-model")

    @patch("extensions.models.models.embeddings_factory")
    def test_propagates_missing_api_key_error(self, mock_factory):
        mock_factory.create_embeddings.side_effect = ValueError("OpenAI API key is required")

        with pytest.raises(ValueError, match="OpenAI API key is required"):
            get_embeddings(provider="OpenAI", model_name="text-embedding-3-small")


class TestGetLlm:
    @patch("extensions.models.models.llm_factory")
    def test_returns_result_from_factory(self, mock_factory):
        expected = MagicMock()
        mock_factory.create_llm.return_value = expected

        result = get_llm(provider="OpenAI", model_name="gpt-4o", api_key="sk-abc")

        assert result is expected

    @patch("extensions.models.models.llm_factory")
    def test_passes_correct_config_to_factory(self, mock_factory):
        get_llm(provider="OpenAI", model_name="gpt-4o", temperature=0.5, api_key="sk-abc")

        _assert_model_config(
            mock_factory.create_llm,
            provider="OpenAI",
            model_name="gpt-4o",
            temperature=0.5,
            api_key="sk-abc",
        )

    @patch("extensions.models.models.llm_factory")
    def test_temperature_defaults_to_zero(self, mock_factory):
        get_llm(provider="OpenAI", model_name="gpt-4o", api_key="sk-abc")

        _assert_model_config(mock_factory.create_llm, temperature=0.0)

    @patch("extensions.models.models.llm_factory")
    def test_api_key_defaults_to_none(self, mock_factory):
        get_llm(provider="Local (Ollama)", model_name="llama3.2")

        _assert_model_config(mock_factory.create_llm, api_key=None)

    @patch("extensions.models.models.llm_factory")
    def test_factory_called_exactly_once(self, mock_factory):
        get_llm(provider="OpenAI", model_name="gpt-4o", api_key="sk-abc")

        mock_factory.create_llm.assert_called_once()

    @patch("extensions.models.models.llm_factory")
    def test_propagates_factory_exception(self, mock_factory):
        mock_factory.create_llm.side_effect = NotImplementedError("Unsupported")

        with pytest.raises(NotImplementedError, match="Unsupported"):
            get_llm(provider="unknown", model_name="some-model")

    @patch("extensions.models.models.llm_factory")
    def test_propagates_missing_api_key_error(self, mock_factory):
        mock_factory.create_llm.side_effect = ValueError("OpenAI API key is required")

        with pytest.raises(ValueError, match="OpenAI API key is required"):
            get_llm(provider="OpenAI", model_name="gpt-4o")
