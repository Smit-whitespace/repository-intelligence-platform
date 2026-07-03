"""Manual Ollama connectivity test."""

from app.core.config.provider import (
    get_settings,
)
from app.indexing.ollama_provider import (
    OllamaEmbeddingProvider,
)


def main() -> None:
    """Run manual embedding test."""

    provider = OllamaEmbeddingProvider(
        get_settings().ollama,
    )

    embeddings = provider.embed(
        [
            "hello world",
            "repository indexing",
            "semantic search",
        ]
    )

    print(
        f"Embeddings: {len(embeddings)}",
    )

    print(
        f"Dimension: {len(embeddings[0].values)}",
    )

    print(
        embeddings[0].values[:5],
    )


if __name__ == "__main__":
    main()