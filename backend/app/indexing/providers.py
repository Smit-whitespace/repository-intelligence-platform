"""Embedding provider abstractions."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from app.indexing.models import EmbeddingVector


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @property
    def identity(
        self,
    ) -> str:
        """Stable identifier of the embedding model, e.g. ``ollama:nomic-embed-text``.

        Recorded in each index it builds. Two providers with the same
        identity must produce comparable vectors. Implementations backed
        by a configurable model must override this so the identity
        changes when the model does.
        """

        return type(
            self,
        ).__name__

    @abstractmethod
    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Generate embeddings."""
