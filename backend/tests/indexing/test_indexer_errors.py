"""Tests for indexing error handling."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from app.indexing.exceptions import EmbeddingError
from app.indexing.indexer import RepositoryIndexer
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.indexing.providers import EmbeddingProvider
from app.indexing.store_resolver import StaticVectorStoreResolver
from app.indexing.stores import VectorStore
from app.indexing.retrieval_models import SearchHit
from app.repository.models import ChunkBoundary
from app.repository.models import (
    RepositoryChunk,
    RepositoryChunkMetadata,
    RepositoryEntry,
)


class BrokenEmbeddingProvider(
    EmbeddingProvider,
):
    """Broken embedding provider."""

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Return an incorrect number of embeddings."""

        return []


class FakeVectorStore(
    VectorStore,
):
    """Fake vector store."""

    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """Store chunks."""

    def search(
        self,
        query_embedding: EmbeddingVector,
        limit: int = 10,
        where: dict | None = None,
    ) -> list[SearchHit]:
        """Return matching indexed chunks."""

        return []

    def get_chunk_ids(
        self,
        where: dict | None = None,
    ) -> list[str]:
        """Return ids of chunks matching the filter."""

        return []

    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        """Delete chunks."""

    def clear(
        self,
    ) -> None:
        """Clear chunks."""


def test_embedding_count_mismatch() -> None:
    """Embedding count mismatch should raise EmbeddingError."""

    entry = RepositoryEntry(
        name="main.py",
        absolute_path=Path("main.py"),
        relative_path=Path("main.py"),
        is_directory=False,
    )

    metadata = RepositoryChunkMetadata(
        relative_path=Path("main.py"),
        language="Python",
        mime_type="text/x-python",
        sha256="abc",
        root_directory="/projects/foo",
    )

    chunk = RepositoryChunk(
        chunk_id="chunk-1",
        entry=entry,
        metadata=metadata,
        content="print('hello')",
         boundary=ChunkBoundary(
            start_line=1,
            end_line=1,
        ),
    )

    indexer = RepositoryIndexer(
        embedding_provider=BrokenEmbeddingProvider(),
        vector_store_resolver=StaticVectorStoreResolver(
            FakeVectorStore(),
        ),
    )

    with pytest.raises(
        EmbeddingError,
    ):
        indexer.index(
            [
                chunk,
            ]
        )