"""Vector store abstractions."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.indexing.retrieval_models import SearchHit


class VectorStore(ABC):
    """Abstract vector store."""

    @abstractmethod
    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """Store indexed chunks."""

    @abstractmethod
    def search(
        self,
        query_embedding: EmbeddingVector,
        limit: int = 10,
    ) -> list[SearchHit]:
        """Return the most similar indexed chunks."""

    @abstractmethod
    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        """Delete indexed chunks."""

    @abstractmethod
    def clear(
        self,
    ) -> None:
        """Remove all indexed chunks."""
