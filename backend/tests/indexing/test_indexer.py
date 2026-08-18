"""Tests for repository indexing."""

from collections.abc import Sequence
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
from app.indexing.retrieval_models import (
    SearchHit,
)
from app.indexing.store_resolver import StaticVectorStoreResolver
from app.indexing.stores import (
    VectorStore,
)
from app.repository.models import (
    ChunkBoundary,
    RepositoryChunk,
    RepositoryChunkMetadata,
    RepositoryEntry,
)


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

        self.chunks: list[
            IndexedChunk
        ] = []

    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """Store indexed chunks."""

        self.chunks.extend(
            chunks,
        )

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

        return [
            chunk.chunk_id
            for chunk in self.chunks
        ]

    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        """Delete indexed chunks."""

        delete_set = set(
            chunk_ids,
        )

        self.chunks = [
            chunk
            for chunk in self.chunks
            if chunk.chunk_id not in delete_set
        ]

    def clear(
        self,
    ) -> None:
        """Remove indexed chunks."""

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
        root_directory="/projects/foo",
    )

    boundary = ChunkBoundary(
        start_line=1,
        end_line=1,
    )

    chunk = RepositoryChunk(
        chunk_id="1",
        entry=entry,
        metadata=metadata,
        boundary=boundary,
        content="print('hello')",
    )

    vector_store = FakeVectorStore()

    result = RepositoryIndexer(
        embedding_provider=FakeEmbeddingProvider(),
        vector_store_resolver=StaticVectorStoreResolver(
            vector_store,
        ),
    ).index(
        [
            chunk,
        ],
    )

    assert result.indexed_chunks == 1

    assert len(
        vector_store.chunks,
    ) == 1

    assert (
        vector_store.chunks[0].chunk_id
        == "1"
    )