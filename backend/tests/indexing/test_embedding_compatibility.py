"""Embedding-model compatibility of project indexes.

End-to-end against a real per-project ChromaDB store: the index records
which embedding model built it, retrieval refuses an index built by a
different model, and an explicit reindex rebuilds it cleanly.
"""

from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from app.indexing.exceptions import IndexIncompatibleError
from app.indexing.indexer import RepositoryIndexer
from app.indexing.models import EmbeddingVector
from app.indexing.providers import EmbeddingProvider
from app.indexing.retrieval_models import SearchQuery
from app.indexing.retrieval_service import RetrievalService
from app.indexing.service import IndexingService
from app.indexing.store_resolver import ProjectChromaStoreResolver
from app.indexing.stores import (
    EMBEDDING_DIMENSION_METADATA_KEY,
    EMBEDDING_MODEL_METADATA_KEY,
)
from app.repository.chunking import RepositoryChunker
from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner


class FakeEmbedder(EmbeddingProvider):
    """Deterministic embedder with a configurable identity and dimension."""

    def __init__(
        self,
        identity: str,
        dimension: int,
    ) -> None:
        self._identity = identity
        self._dimension = dimension

    @property
    def identity(
        self,
    ) -> str:
        return self._identity

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        return [
            EmbeddingVector(
                values=[
                    float(len(text) % 7 + 1),
                ]
                * self._dimension,
            )
            for text in texts
        ]


@pytest.fixture
def resolver() -> Iterator[ProjectChromaStoreResolver]:
    store_resolver = ProjectChromaStoreResolver(
        collection_name="repository_chunks",
    )

    yield store_resolver

    # Release Chroma file handles so the temp directory can be removed.
    store_resolver.close_all()


@pytest.fixture
def project(
    tmp_path: Path,
) -> Path:
    (tmp_path / "main.py").write_text(
        "def handler():\n    return 'hello'\n",
        encoding="utf-8",
    )

    (tmp_path / "README.md").write_text(
        "# Demo\n\nA tiny project.\n",
        encoding="utf-8",
    )

    return tmp_path


def _index(
    root: Path,
    embedder: EmbeddingProvider,
    resolver: ProjectChromaStoreResolver,
) -> None:
    IndexingService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
        document_loader=RepositoryDocumentLoader(),
        chunker=RepositoryChunker(),
        indexer=RepositoryIndexer(
            embedding_provider=embedder,
            vector_store_resolver=resolver,
        ),
    ).index_repository(
        root,
    )


def _search(
    root: Path,
    embedder: EmbeddingProvider,
    resolver: ProjectChromaStoreResolver,
) -> int:
    response = RetrievalService(
        embedding_provider=embedder,
        vector_store_resolver=resolver,
    ).search(
        SearchQuery(
            query="handler",
            root_directory=str(
                root.resolve(),
            ),
        ),
    )

    return len(
        response.results,
    )


def _metadata(
    root: Path,
    resolver: ProjectChromaStoreResolver,
) -> dict:
    store = resolver.for_project(
        str(
            root.resolve(),
        ),
    )

    assert store is not None

    metadata = store.get_index_metadata()

    assert metadata is not None

    return metadata


def test_indexing_records_embedding_model_and_dimension(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    _index(
        project,
        FakeEmbedder("fake:model-a", 4),
        resolver,
    )

    metadata = _metadata(
        project,
        resolver,
    )

    assert metadata[EMBEDDING_MODEL_METADATA_KEY] == "fake:model-a"

    assert metadata[EMBEDDING_DIMENSION_METADATA_KEY] == 4


def test_search_with_matching_model_works(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    embedder = FakeEmbedder("fake:model-a", 4)

    _index(
        project,
        embedder,
        resolver,
    )

    assert _search(project, embedder, resolver) > 0


def test_search_with_different_model_is_a_clear_error(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    _index(
        project,
        FakeEmbedder("fake:model-a", 4),
        resolver,
    )

    with pytest.raises(
        IndexIncompatibleError,
    ) as error:
        _search(
            project,
            FakeEmbedder("fake:model-b", 8),
            resolver,
        )

    message = str(error.value)

    assert "fake:model-a" in message

    assert "fake:model-b" in message

    assert "Reindex" in message


def test_reindex_with_new_model_rebuilds_the_index(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    """A different vector dimension would fail in Chroma unless cleared."""

    _index(
        project,
        FakeEmbedder("fake:model-a", 4),
        resolver,
    )

    new_embedder = FakeEmbedder("fake:model-b", 8)

    _index(
        project,
        new_embedder,
        resolver,
    )

    metadata = _metadata(
        project,
        resolver,
    )

    assert metadata[EMBEDDING_MODEL_METADATA_KEY] == "fake:model-b"

    assert metadata[EMBEDDING_DIMENSION_METADATA_KEY] == 8

    assert _search(project, new_embedder, resolver) > 0


def test_legacy_index_is_searchable_then_rebuilt_on_reindex(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    """Indexes built before tracking keep working until the next reindex."""

    embedder = FakeEmbedder("fake:model-a", 4)

    _index(
        project,
        embedder,
        resolver,
    )

    # Simulate an index from before compatibility tracking existed.
    store = resolver.for_project(
        str(
            project.resolve(),
        ),
    )

    assert store is not None

    store._collection.modify(  # noqa: SLF001
        metadata={
            "legacy": True,
        },
    )

    assert EMBEDDING_MODEL_METADATA_KEY not in _metadata(project, resolver)

    assert _search(project, embedder, resolver) > 0

    _index(
        project,
        embedder,
        resolver,
    )

    assert (
        _metadata(project, resolver)[EMBEDDING_MODEL_METADATA_KEY]
        == "fake:model-a"
    )


def test_ollama_identity_follows_the_configured_model() -> None:
    from app.core.config.models import OllamaSettings
    from app.indexing.ollama_provider import OllamaEmbeddingProvider

    provider = OllamaEmbeddingProvider(
        OllamaSettings(
            embedding_model="mxbai-embed-large",
        ),
    )

    assert provider.identity == "ollama:mxbai-embed-large"
