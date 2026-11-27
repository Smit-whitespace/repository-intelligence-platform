"""Vector store abstractions."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.indexing.retrieval_models import SearchHit


EMBEDDING_MODEL_METADATA_KEY = "rip_embedding_model"
"""Index metadata key: identity of the embedding model that built it."""

EMBEDDING_DIMENSION_METADATA_KEY = "rip_embedding_dimension"
"""Index metadata key: dimension of the stored vectors."""


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
        where: dict | None = None,
    ) -> list[SearchHit]:
        """Return the most similar indexed chunks."""

    @abstractmethod
    def get_chunk_ids(
        self,
        where: dict | None = None,
    ) -> list[str]:
        """Return chunk ids matching the filter."""

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

    def get_index_metadata(
        self,
    ) -> dict[str, str | int | float | bool] | None:
        """Return metadata describing how this index was built.

        ``None`` means the store does not track index metadata at all, so
        embedding compatibility cannot be checked for it. A store that
        does track it returns a dict, which is empty for an index built
        before compatibility tracking existed.
        """

        return None

    def get_chunk_ids_by_path(
        self,
        where: dict | None = None,
    ) -> dict[str, set[str]] | None:
        """Group indexed chunk ids by their file's relative path.

        ``None`` when the store cannot report this; indexing then cannot
        protect the existing chunks of a file that fails temporarily.
        """

        del where

        return None

    def get_file_hashes(
        self,
        where: dict | None = None,
    ) -> dict[str, str] | None:
        """Map each indexed file's relative path to its stored SHA-256.

        ``None`` when the store cannot report this; freshness checks then
        have nothing to compare the files on disk against.
        """

        del where

        return None

    def set_index_metadata(
        self,
        metadata: dict[str, str | int | float | bool],
    ) -> None:
        """Merge ``metadata`` into the index metadata.

        A no-op for stores that do not track index metadata.
        """

        del metadata
