"""Embedding provider abstractions."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from app.indexing.models import EmbeddingVector


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @abstractmethod
    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Generate embeddings."""