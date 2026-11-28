"""Shared fixtures and helpers for the indexing tests (real ChromaDB).

A counting embedder records every text it embeds, so each test can
assert exactly which content was (re-)embedded.
"""

from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from app.indexing.indexer import RepositoryIndexer
from app.indexing.models import EmbeddingVector, IndexingResult
from app.indexing.providers import EmbeddingProvider
from app.indexing.service import IndexingService
from app.indexing.store_resolver import ProjectChromaStoreResolver
from app.repository.chunking import RepositoryChunker
from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner


class CountingEmbedder(EmbeddingProvider):
    """Records every embedded text."""

    def __init__(
        self,
        identity: str = "fake:model-a",
    ) -> None:
        self._identity = identity

        self.embedded: list[str] = []

    @property
    def identity(
        self,
    ) -> str:
        return self._identity

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        self.embedded.extend(
            texts,
        )

        return [
            EmbeddingVector(
                values=[
                    float(len(text) % 5 + 1),
                    1.0,
                    0.5,
                ],
            )
            for text in texts
        ]


@pytest.fixture
def resolver() -> Iterator[ProjectChromaStoreResolver]:
    store_resolver = ProjectChromaStoreResolver(
        collection_name="repository_chunks",
    )

    yield store_resolver

    store_resolver.close_all()


@pytest.fixture
def project(
    tmp_path: Path,
) -> Path:
    (tmp_path / "main.py").write_text(
        "def main():\n    return 'main'\n",
        encoding="utf-8",
    )

    (tmp_path / "utils.py").write_text(
        "def helper():\n    return 'helper'\n",
        encoding="utf-8",
    )

    return tmp_path


def _service(
    embedder: EmbeddingProvider,
    resolver: ProjectChromaStoreResolver,
) -> IndexingService:
    return IndexingService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
        document_loader=RepositoryDocumentLoader(),
        chunker=RepositoryChunker(),
        indexer=RepositoryIndexer(
            embedding_provider=embedder,
            vector_store_resolver=resolver,
        ),
    )


def _index(
    root: Path,
    embedder: EmbeddingProvider,
    resolver: ProjectChromaStoreResolver,
) -> IndexingResult:
    return _service(
        embedder,
        resolver,
    ).index_repository(
        root,
    )


def _indexed_paths(
    root: Path,
    resolver: ProjectChromaStoreResolver,
) -> set[str]:
    store = resolver.for_project(
        str(
            root.resolve(),
        ),
    )

    assert store is not None

    result = store._collection.get(  # noqa: SLF001
        include=[
            "metadatas",
        ],
    )

    return {
        Path(
            metadata["relative_path"],
        ).as_posix()
        for metadata in result["metadatas"]
    }
