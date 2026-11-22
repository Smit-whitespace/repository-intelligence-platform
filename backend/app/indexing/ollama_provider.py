"""Ollama embedding provider."""

from collections.abc import Sequence

from ollama import Client
from ollama import ResponseError

from app.core.config.models import OllamaSettings
from app.indexing.exceptions import EmbeddingError
from app.indexing.models import EmbeddingVector
from app.indexing.providers import EmbeddingProvider


class OllamaEmbeddingProvider(
    EmbeddingProvider,
):
    """Embedding provider backed by Ollama."""

    def __init__(
        self,
        settings: OllamaSettings,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the Ollama client.

        ``model`` and ``base_url`` come from the model configuration;
        without them the ``LOC_OLLAMA_*`` settings apply.
        """

        self._settings = settings

        self._model = model or settings.embedding_model

        self._client = Client(
            host=base_url or settings.base_url,
        )

    @property
    def identity(
        self,
    ) -> str:
        """Return ``ollama:<model>`` for the configured embedding model."""

        return f"ollama:{self._model}"

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Generate embeddings using Ollama."""

        try:
            response = self._client.embed(
                model=self._model,
                input=list(
                    texts,
                ),
            )

        except ResponseError as error:
            raise EmbeddingError(
                str(
                    error,
                ),
            ) from error

        return [
            EmbeddingVector(
                values=list(
                    embedding,
                ),
            )
            for embedding in response.embeddings
        ]
