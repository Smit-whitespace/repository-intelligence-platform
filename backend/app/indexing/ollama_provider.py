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
    ) -> None:
        """Initialize the Ollama client."""

        self._settings = settings

        self._client = Client(
            host=settings.base_url,
        )

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Generate embeddings using Ollama."""

        try:
            response = self._client.embed(
                model=self._settings.embedding_model,
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
