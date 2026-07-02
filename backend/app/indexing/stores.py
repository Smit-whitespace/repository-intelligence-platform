"""Vector store abstractions."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from app.indexing.models import IndexedChunk


class VectorStore(ABC):
    """Abstract vector store."""

    @abstractmethod
    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """Store indexed chunks."""

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