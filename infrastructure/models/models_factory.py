"""Model factory module for LLM and embedding initialization.

This module provides factory functions for creating chat language models
and embedding models for both local (Ollama) and cloud (OpenAI) providers.
"""
from enum import Enum

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .model_config import ModelConfig


class Provider(str, Enum):
    """
    This enum contains possible llm and embeddings provider currently: 
    'Local (Ollama)' or 'OpenAI'.
    """
    OPENAI = "OpenAI"
    OLLAMA = "Local (Ollama)"


class EmbeddingsFactory:
    def __init__(self):
        self._embeddings_builders = {
            Provider.OPENAI: self._openai_embeddings,
            Provider.OLLAMA: self._ollama_embeddings
        }

    def create_embeddings(self, config: ModelConfig):
        """
        Create an embeddings model instance based on the provider.

        Args:
            provider: 'Local (Ollama)' or 'OpenAI'.
            model_name: Name of the model (e.g. 'llama3.2' or 'text-embedding-3-small').
            api_key: OpenAI API Key (required if provider is OpenAI).

        Returns:
            Embeddings: Configured embeddings object.
        """
        builder = self._embeddings_builders.get(config.provider)
        if builder is None:
            raise NotImplementedError(
                f"Unsupported embeddings provider: '{config.provider}'. "
                f"Supported: {sorted(self._embeddings_builders)}"
            )
        return builder(config)

    def _openai_embeddings(self, config: ModelConfig):
        _require_api_key(config, "OpenAI embeddings")
        return OpenAIEmbeddings(model=config.model_name, api_key=config.api_key)

    def _ollama_embeddings(self, config: ModelConfig):
        return OllamaEmbeddings(
            model=config.model_name, base_url=config.ollama_base_url
        )


class LlmFactory:
    def __init__(self):
        self._llm_builders = {
            Provider.OPENAI: self._openai_llm,
            Provider.OLLAMA: self._ollama_llm,
        }

    def create_llm(self, config: ModelConfig):
        """
        Create a chat language model instance based on the provider.

        Args:
            provider: 'Local (Ollama)' or 'OpenAI'.
            model_name: Name of the model (e.g. 'gpt-4o' or 'llama3.2').
            temperature: Sampling temperature.
            api_key: OpenAI API Key (required if provider is OpenAI).

        Returns:
            BaseChatModel: Configured chat model.
        """
        builder = self._llm_builders.get(config.provider)
        if builder is None:
            raise NotImplementedError(
                f"Unsupported LLM provider: '{config.provider}'. "
                f"Supported: {sorted(self._llm_builders)}"
            )
        return builder(config)

    @staticmethod
    def _openai_llm(config: ModelConfig):
        _require_api_key(config, "OpenAI LLM")
        return ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            api_key=config.api_key,
        )

    @staticmethod
    def _ollama_llm(config: ModelConfig):
        return ChatOllama(
            model=config.model_name,
            temperature=config.temperature,
            base_url=config.ollama_base_url,
        )


def _require_api_key(config: ModelConfig, context: str) -> None:
    if not config.api_key:
        raise ValueError(f"OpenAI API key is required for {context}.")


# module level singeltons
llm_factory: LlmFactory = LlmFactory()
embeddings_factory: EmbeddingsFactory = EmbeddingsFactory()
