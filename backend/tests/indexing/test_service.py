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
from app.indexing.store_resolver import StaticVectorStoreResolver
from app.indexing.stores import VectorStore
from app.repository.chunking import RepositoryChunker
from app.repository.documents import (
    RepositoryDocument,
    RepositoryDocumentLoader,
)
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import (
    RepositoryChunk,
    RepositoryEntry,
)
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
    """Fake vector store mimicking Chroma semantics."""

    def __init__(
        self,
    ) -> None:
        """Initialize fake vector store."""

        self.chunks: list[
            IndexedChunk
        ] = []

        self.deleted_chunk_ids: list[
            str
        ] = []

    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """Store indexed chunks, ignoring existing ids."""

        existing_ids = {
            chunk.chunk_id
            for chunk in self.chunks
        }

        for chunk in chunks:
            if (
                chunk.chunk_id
                in existing_ids
            ):
                continue

            self.chunks.append(
                chunk,
            )

            existing_ids.add(
                chunk.chunk_id,
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
            if self._matches(
                chunk,
                where,
            )
        ]

    @staticmethod
    def _matches(
        chunk: IndexedChunk,
        where: dict | None,
    ) -> bool:
        """Return whether a chunk matches the filter."""

        if where is None:
            return True

        metadata = chunk.metadata.model_dump(
            mode="json",
        )

        return all(
            metadata.get(key) == value
            for key, value in where.items()
        )

    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        """Delete chunks."""

        delete_set = set(
            chunk_ids,
        )

        self.chunks = [
            chunk
            for chunk in self.chunks
            if chunk.chunk_id not in delete_set
        ]

        self.deleted_chunk_ids.extend(
            chunk_ids,
        )

    def clear(
        self,
    ) -> None:
        """Clear indexed chunks."""

        self.chunks.clear()


class FailingDocumentLoader(
    RepositoryDocumentLoader,
):
    """Document loader that fails for a specific filename."""

    def __init__(
        self,
        fail_on: str,
    ) -> None:
        """Initialize with filename to fail on."""

        super().__init__()

        self._fail_on = fail_on

    def load(
        self,
        entry: RepositoryEntry,
    ) -> RepositoryDocument:
        """Load a document, failing if filename matches."""

        if entry.name == self._fail_on:
            raise ValueError(
                f"Simulated failure: {entry.name}",
            )

        return super().load(
            entry,
        )


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
        tmp_path / "module.mjs"
    ).write_text(
        "export const VERSION = '1.0.0';",
        encoding="utf-8",
    )

    (
        tmp_path / "config.cjs"
    ).write_text(
        "module.exports = { port: 3000 };",
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
            vector_store_resolver=StaticVectorStoreResolver(
                vector_store,
            ),
        ),
    )

    result = service.index_repository(
        tmp_path,
    )

    assert result.scanned_files == 6

    assert result.indexed_files == 5

    assert result.skipped_files == 1

    assert result.failed_files == 0

    assert result.indexed_chunks > 0

    assert len(
        vector_store.chunks,
    ) == result.indexed_chunks

    mjs_chunks = [
        c
        for c in vector_store.chunks
        if c.metadata.relative_path.name
        == "module.mjs"
    ]

    assert len(mjs_chunks) > 0

    mjs_chunk = mjs_chunks[0]

    assert mjs_chunk.metadata.language == "JavaScript"

    assert mjs_chunk.metadata.mime_type == "text/javascript"

    cjs_chunks = [
        c
        for c in vector_store.chunks
        if c.metadata.relative_path.name
        == "config.cjs"
    ]

    assert len(cjs_chunks) > 0

    cjs_chunk = cjs_chunks[0]

    assert cjs_chunk.metadata.language == "JavaScript"

    assert cjs_chunk.metadata.mime_type == "text/javascript"

    diagnostics = result.diagnostics

    assert diagnostics is not None

    assert (
        diagnostics.total_files_discovered
        == 6
    )

    assert diagnostics.text_files_detected == 5

    assert (
        diagnostics.total_chunks_created
        == result.indexed_chunks
    )

    assert (
        diagnostics.indexing_duration_ms >= 0
    )

    assert (
        diagnostics.failed_files_details == []
    )


def test_index_repository_with_failure(
    tmp_path: Path,
) -> None:
    """A single indexing failure should not abort remaining files."""

    (
        tmp_path / "main.py"
    ).write_text(
        "def main():\n    print('hello')",
        encoding="utf-8",
    )

    (
        tmp_path / "broken.py"
    ).write_text(
        "x = 1",
        encoding="utf-8",
    )

    (
        tmp_path / "utils.py"
    ).write_text(
        "def add(a, b):\n    return a + b",
        encoding="utf-8",
    )

    vector_store = FakeVectorStore()

    service = IndexingService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
        document_loader=FailingDocumentLoader(
            fail_on="broken.py",
        ),
        chunker=RepositoryChunker(),
        indexer=RepositoryIndexer(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store_resolver=StaticVectorStoreResolver(
                vector_store,
            ),
        ),
    )

    result = service.index_repository(
        tmp_path,
    )

    assert result.indexed_files == 2

    assert result.failed_files == 1

    assert result.skipped_files == 0

    assert result.indexed_chunks > 0

    diagnostics = result.diagnostics

    assert diagnostics is not None

    assert diagnostics.text_files_detected == 3

    assert (
        diagnostics.total_chunks_created
        == result.indexed_chunks
    )

    assert (
        diagnostics.indexing_duration_ms >= 0
    )

    assert len(
        diagnostics.failed_files_details,
    ) == 1

    detail = diagnostics.failed_files_details[0]

    assert detail.relative_path == "broken.py"

    assert detail.stage == "load"

    assert (
        detail.exception_type
        == "ValueError"
    )

    assert (
        "Simulated failure: broken.py"
        in detail.message
    )


def test_index_repository_failure_at_chunking(
    tmp_path: Path,
) -> None:
    """A chunking failure should report stage='chunking'."""

    class FailingChunker(
        RepositoryChunker,
    ):
        """Chunker that fails for a specific filename."""

        def chunk(
            self,
            document: RepositoryDocument,
        ) -> list[RepositoryChunk]:
            if (
                document.entry.name
                == "bad.py"
            ):
                raise RuntimeError(
                    f"Chunk failed: {document.entry.name}",
                )

            return super().chunk(
                document,
            )

    (
        tmp_path / "good.py"
    ).write_text(
        "x = 1",
        encoding="utf-8",
    )

    (
        tmp_path / "bad.py"
    ).write_text(
        "y = 2",
        encoding="utf-8",
    )

    vector_store = FakeVectorStore()

    service = IndexingService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
        document_loader=RepositoryDocumentLoader(),
        chunker=FailingChunker(),
        indexer=RepositoryIndexer(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store_resolver=StaticVectorStoreResolver(
                vector_store,
            ),
        ),
    )

    result = service.index_repository(
        tmp_path,
    )

    assert result.indexed_files == 1

    assert result.failed_files == 1

    diagnostics = result.diagnostics

    assert diagnostics is not None

    assert len(
        diagnostics.failed_files_details,
    ) == 1

    detail = diagnostics.failed_files_details[0]

    assert detail.relative_path == "bad.py"

    assert detail.stage == "chunking"

    assert detail.exception_type == "RuntimeError"


def test_index_repository_failure_at_indexing(
    tmp_path: Path,
) -> None:
    """An indexing (embedding/storage) failure should report stage='indexing'."""

    class FailingEmbeddingProvider(
        FakeEmbeddingProvider,
    ):
        """Embedding provider that fails for a specific text."""

        def embed(
            self,
            texts: Sequence[str],
        ) -> list[EmbeddingVector]:
            if any(
                "bad" in t
                for t in texts
            ):
                raise RuntimeError(
                    "Embedding failed",
                )

            return super().embed(
                texts,
            )

    (
        tmp_path / "good.py"
    ).write_text(
        "x = 1",
        encoding="utf-8",
    )

    (
        tmp_path / "bad.py"
    ).write_text(
        "# bad file",
        encoding="utf-8",
    )

    vector_store = FakeVectorStore()

    service = IndexingService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
        document_loader=RepositoryDocumentLoader(),
        chunker=RepositoryChunker(),
        indexer=RepositoryIndexer(
            embedding_provider=FailingEmbeddingProvider(),
            vector_store_resolver=StaticVectorStoreResolver(
                vector_store,
            ),
        ),
    )

    result = service.index_repository(
        tmp_path,
    )

    assert result.indexed_files == 1

    assert result.failed_files == 1

    diagnostics = result.diagnostics

    assert diagnostics is not None

    assert len(
        diagnostics.failed_files_details,
    ) == 1

    detail = diagnostics.failed_files_details[0]

    assert detail.relative_path == "bad.py"

    assert detail.stage == "indexing"

    assert detail.exception_type == "RuntimeError"