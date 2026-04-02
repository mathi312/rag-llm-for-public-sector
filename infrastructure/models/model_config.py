import os
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelConfig:
    """
    A value object that carries every parameter needed to build a model or embeddings client.
    """

    provider: str
    model_name: str
    temperature: float = 0.0
    api_key: str | None = None
    ollama_base_url: str = ""

    def __post_init__(self) -> None:
        if not self.ollama_base_url:
            object.__setattr__(
                self,
                "ollama_base_url",
                os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )
