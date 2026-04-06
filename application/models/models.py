from infrastructure.models import ModelConfig, llm_factory, embeddings_factory


def get_embeddings(provider: str, model_name: str, api_key: str = None):
    """
    Get an embeddings model instance based on the provider.
    """
    config = ModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key
    )

    embeddings = embeddings_factory.create_embeddings(config=config)

    return embeddings

def get_llm(provider: str, model_name: str, temperature: float = 0.0, api_key: str = None):
    """
    Get a chat language model instance based on the provider.
    """
    config = ModelConfig(
        provider=provider,
        model_name=model_name,
        temperature=temperature,
        api_key=api_key
    )

    llm = llm_factory.create_llm(config=config)

    return llm
