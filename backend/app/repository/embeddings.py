"""Embedding provider abstractions."""

from abc import ABC
from abc import abstractmethod


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @abstractmethod
    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""