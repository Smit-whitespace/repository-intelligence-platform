"""Integration tests for indexing service."""

from collections.abc import Sequence
from pathlib import Path

from app.indexing.indexer import RepositoryIndexer
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.indexing.providers import EmbeddingProvider
from app.indexing.service import IndexingService
from app.indexing.stores import VectorStore
from app.repository.chunking import RepositoryChunker
from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner
from app.indexing.retrieval_models import SearchHit

class FakeEmbeddingProvider(
    EmbeddingProvider,
):
    """Fake embedding provider."""

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Return deterministic embeddings."""

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
        """Initialize fake vector store."""

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
    ) -> list[SearchHit]:
        """Return matching indexed chunks."""

        return []

    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        """Delete chunks."""

    def clear(
        self,
    ) -> None:
        """Clear indexed chunks."""

        self.chunks.clear()


def test_index_repository(
    tmp_path: Path,
) -> None:
    """Index a repository end-to-end."""

    (
        tmp_path / "main.py"
    ).write_text(
        "def main():\n    print('hello')",
        encoding="utf-8",
    )

    (
        tmp_path / "utils.py"
    ).write_text(
        "def add(a, b):\n    return a + b",
        encoding="utf-8",
    )

    (
        tmp_path / "README.md"
    ).write_text(
        "# Local OpenClaw",
        encoding="utf-8",
    )

    (
        tmp_path / "image.png"
    ).write_bytes(
        b"\x89PNG\r\n\x1a\n",
    )

    vector_store = FakeVectorStore()

    service = IndexingService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
        document_loader=RepositoryDocumentLoader(),
        chunker=RepositoryChunker(),
        indexer=RepositoryIndexer(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=vector_store,
        ),
    )

    result = service.index_repository(
        tmp_path,
    )

    assert result.scanned_files == 4

    assert result.indexed_files == 3

    assert result.skipped_files == 1

    assert result.failed_files == 0

    assert result.indexed_chunks > 0

    assert len(
        vector_store.chunks,
    ) == result.indexed_chunks