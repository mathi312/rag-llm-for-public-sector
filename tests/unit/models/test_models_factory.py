import pytest
from unittest.mock import MagicMock, patch

from extensions.models.models_factory import _require_api_key, LlmFactory, EmbeddingsFactory, Provider


def make_config(
    provider=Provider.OPENAI,
    model_name="gpt-4o",
    temperature=0.7,
    api_key="sk-test",
    ollama_base_url="http://localhost:11434",
):
    config = MagicMock()
    config.provider = provider
    config.model_name = model_name
    config.temperature = temperature
    config.api_key = api_key
    config.ollama_base_url = ollama_base_url
    return config


class TestEmbeddingsFactory:
    def setup_method(self):
        self.factory = EmbeddingsFactory()

    @patch("extensions.models.models_factory.OpenAIEmbeddings")
    def test_create_openai_embeddings_returns_instance(self, mock_embeddings):
        config = make_config(provider=Provider.OPENAI)
        result = self.factory.create_embeddings(config)
        mock_embeddings.assert_called_once_with(
            model=config.model_name,
            api_key=config.api_key,
        )
        assert result is mock_embeddings.return_value

    @patch("extensions.models.models_factory.OpenAIEmbeddings")
    def test_create_openai_embeddings_raises_without_api_key(self, _mock):
        config = make_config(provider=Provider.OPENAI, api_key=None)
        with pytest.raises(ValueError, match="OpenAI API key is required for OpenAI embeddings"):
            self.factory.create_embeddings(config)

    @patch("extensions.models.models_factory.OllamaEmbeddings")
    def test_create_ollama_embeddings_returns_instance(self, mock_embeddings):
        config = make_config(provider=Provider.OLLAMA, api_key=None)
        result = self.factory.create_embeddings(config)
        mock_embeddings.assert_called_once_with(
            model=config.model_name,
            base_url=config.ollama_base_url,
        )
        assert result is mock_embeddings.return_value

    @patch("extensions.models.models_factory.OllamaEmbeddings")
    def test_create_ollama_embeddings_does_not_require_api_key(self, _mock):
        config = make_config(provider=Provider.OLLAMA, api_key=None)
        self.factory.create_embeddings(config)  # should not raise-

    def test_create_embeddings_raises_for_unsupported_provider(self):
        config = make_config(provider="unsupported_provider")
        with pytest.raises(NotImplementedError, match="Unsupported embeddings provider"):
            self.factory.create_embeddings(config)


class TestLlmFactory:
    def setup_method(self):
        self.factory = LlmFactory()

    @patch("extensions.models.models_factory.ChatOpenAI")
    def test_create_openai_llm_returns_instance(self, mock_chat_openai):
        config = make_config(provider=Provider.OPENAI)
        result = self.factory.create_llm(config)
        mock_chat_openai.assert_called_once_with(
            model=config.model_name,
            temperature=config.temperature,
            api_key=config.api_key,
        )
        assert result is mock_chat_openai.return_value

    @patch("extensions.models.models_factory.ChatOpenAI")
    def test_create_openai_llm_raises_without_api_key(self, _mock):
        config = make_config(provider=Provider.OPENAI, api_key=None)
        with pytest.raises(ValueError, match="OpenAI API key is required for OpenAI LLM"):
            self.factory.create_llm(config)

    @patch("extensions.models.models_factory.ChatOllama")
    def test_create_ollama_llm_returns_instance(self, mock_chat_ollama):
        config = make_config(provider=Provider.OLLAMA, api_key=None)
        result = self.factory.create_llm(config)
        mock_chat_ollama.assert_called_once_with(
            model=config.model_name,
            temperature=config.temperature,
            base_url=config.ollama_base_url,
        )
        assert result is mock_chat_ollama.return_value

    @patch("extensions.models.models_factory.ChatOllama")
    def test_create_ollama_llm_does_not_require_api_key(self, _mock):
        config = make_config(provider=Provider.OLLAMA, api_key=None)
        self.factory.create_llm(config)

    def test_create_llm_raises_for_unsupported_provider(self):
        config = make_config(provider="unsupported_provider")
        with pytest.raises(NotImplementedError, match="Unsupported LLM provider"):
            self.factory.create_llm(config)


class TestRequireApiKey:
    def test_raises_when_api_key_missing(self):
        config = make_config(api_key=None)
        with pytest.raises(ValueError, match="OpenAI API key is required for TestCtx"):
            _require_api_key(config, "TestCtx")

    def test_raises_when_api_key_empty_string(self):
        config = make_config(api_key="")
        with pytest.raises(ValueError, match="OpenAI API key is required for TestCtx"):
            _require_api_key(config, "TestCtx")

    def test_passes_when_api_key_present(self):
        config = make_config(api_key="sk-valid")
        _require_api_key(config, "TestCtx") 

class TestModuleSingletons:
    def test_llm_factory_singleton_is_llm_factory(self):
        from extensions.models.models_factory import llm_factory
        assert isinstance(llm_factory, LlmFactory)

    def test_embeddings_factory_singleton_is_embeddings_factory(self):
        from extensions.models.models_factory import embeddings_factory
        assert isinstance(embeddings_factory, EmbeddingsFactory)
