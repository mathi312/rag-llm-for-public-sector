import pytest
import os
from unittest.mock import patch

from extensions.models.model_config import ModelConfig


OLLAMA_DEFAULT = "http://localhost:11434"
OLLAMA_CUSTOM = "http://my-ollama-server:11434"
OLLAMA_ENV = "http://env-ollama:11434"


class TestDefaults:
    def test_temperature_defaults_to_zero(self):
        config = ModelConfig(provider="OpenAI", model_name="gpt-4o")
        assert config.temperature == 0.0

    def test_api_key_defaults_to_none(self):
        config = ModelConfig(provider="OpenAI", model_name="gpt-4o")
        assert config.api_key is None

    def test_ollama_base_url_defaults_to_hardcoded_when_env_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OLLAMA_BASE_URL", None)
            config = ModelConfig(provider="Local (Ollama)", model_name="llama3.2")
        assert config.ollama_base_url == OLLAMA_DEFAULT

    def test_ollama_base_url_uses_env_var_when_set(self):
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": OLLAMA_ENV}):
            config = ModelConfig(provider="Local (Ollama)", model_name="llama3.2")
        assert config.ollama_base_url == OLLAMA_ENV


class TestExplicitValues:
    def test_explicit_temperature(self):
        config = ModelConfig(provider="OpenAI", model_name="gpt-4o", temperature=0.9)
        assert config.temperature == 0.9

    def test_explicit_api_key(self):
        config = ModelConfig(provider="OpenAI", model_name="gpt-4o", api_key="sk-abc")
        assert config.api_key == "sk-abc"

    def test_explicit_ollama_base_url_is_not_overwritten(self):
        config = ModelConfig(
            provider="Local (Ollama)",
            model_name="llama3.2",
            ollama_base_url=OLLAMA_CUSTOM,
        )
        assert config.ollama_base_url == OLLAMA_CUSTOM

    def test_explicit_ollama_base_url_takes_priority_over_env(self):
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": OLLAMA_ENV}):
            config = ModelConfig(
                provider="Local (Ollama)",
                model_name="llama3.2",
                ollama_base_url=OLLAMA_CUSTOM,
            )
        assert config.ollama_base_url == OLLAMA_CUSTOM
