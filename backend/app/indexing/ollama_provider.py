"""Ollama embedding provider."""

from collections.abc import Sequence

import httpx
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
        without them the ``RIP_OLLAMA_*`` settings apply.
        """

        self._settings = settings

        self._model = model or settings.embedding_model

        self._host = base_url or settings.base_url

        self._client = Client(
            host=self._host,
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

        except (ConnectionError, httpx.HTTPError) as error:
            # The client raises the built-in ConnectionError when Ollama is
            # not running; left unhandled it became a bare HTTP 500.
            raise EmbeddingError(
                f"Could not reach Ollama at {self._host}. Is it running?",
            ) from error

        return [
            EmbeddingVector(
                values=list(
                    embedding,
                ),
            )
            for embedding in response.embeddings
        ]
