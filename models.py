"""Model factory module for LLM and embedding initialization.

This module provides factory functions for creating chat language models
and embedding models for both local (Ollama) and cloud (OpenAI) providers.
"""

import os
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Configurable URL for local Ollama instance
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_embeddings(provider: str, model_name: str, api_key: str = None):
    """Create an embeddings model instance based on the provider.

    Args:
        provider: 'Local (Ollama)' or 'OpenAI'.
        model_name: Name of the model (e.g. 'llama3.2' or 'text-embedding-3-small').
        api_key: OpenAI API Key (required if provider is OpenAI).

    Returns:
        Embeddings: Configured embeddings object.
    """
    if provider == "OpenAI":
        if not api_key:
            raise ValueError("OpenAI API Key is required for OpenAI embeddings.")
        return OpenAIEmbeddings(model=model_name, api_key=api_key)
    
    # Default to Local Ollama
    return OllamaEmbeddings(model=model_name, base_url=OLLAMA_BASE_URL)


def get_llm(provider: str, model_name: str, temperature: float = 0.0, api_key: str = None):
    """Create a chat language model instance based on the provider.

    Args:
        provider: 'Local (Ollama)' or 'OpenAI'.
        model_name: Name of the model (e.g. 'gpt-4o' or 'llama3.2').
        temperature: Sampling temperature.
        api_key: OpenAI API Key (required if provider is OpenAI).

    Returns:
        BaseChatModel: Configured chat model.
    """
    if provider == "OpenAI":
        if not api_key:
            raise ValueError("OpenAI API Key is required for OpenAI models.")
        return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)

    # Default to Local Ollama
    return ChatOllama(model=model_name, temperature=temperature, base_url=OLLAMA_BASE_URL)
