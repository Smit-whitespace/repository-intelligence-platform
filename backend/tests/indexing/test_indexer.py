"""Tests for repository indexing."""

from pathlib import Path

from app.indexing.indexer import (
    RepositoryIndexer,
)
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.indexing.providers import (
    EmbeddingProvider,
)
from app.indexing.stores import (
    VectorStore,
)
from app.repository.models import (
    RepositoryChunk,
    RepositoryChunkMetadata,
    RepositoryEntry,
)

from collections.abc import Sequence


class FakeEmbeddingProvider(
    EmbeddingProvider,
):
    """Fake embedding provider."""

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Return fake embeddings."""

        return [
            EmbeddingVector(
                values=[1.0],
            )
            for _ in texts
        ]


class FakeVectorStore(
    VectorStore,
):
    """Fake vector store."""

    def __init__(
        self,
    ) -> None:
        """Initialize the fake vector store."""
        self.chunks: list[IndexedChunk] = []

    def add(
        self,
        chunks,
    ):
        self.chunks.extend(
            chunks,
        )

    def delete(
        self,
        chunk_ids,
    ):
        pass

    def clear(
        self,
    ):
        self.chunks.clear()


def test_index_repository_chunk() -> None:
    """Repository chunk should be indexed."""

    entry = RepositoryEntry(
        name="main.py",
        absolute_path=Path(
            "main.py",
        ),
        relative_path=Path(
            "main.py",
        ),
        is_directory=False,
    )

    metadata = RepositoryChunkMetadata(
        relative_path=Path(
            "main.py",
        ),
        language="Python",
        mime_type="text/x-python",
        sha256="abc",
    )

    chunk = RepositoryChunk(
        chunk_id="1",
        entry=entry,
        metadata=metadata,
        content="print('hello')",
        start_line=1,
        end_line=1,
    )

    vector_store = FakeVectorStore()

    result = RepositoryIndexer(
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=vector_store,
    ).index(
        [
            chunk,
        ]
    )

    assert result.indexed_chunks == 1

    assert len(
        vector_store.chunks,
    ) == 1

    assert (
        vector_store.chunks[0].chunk_id
        == "1"
    )