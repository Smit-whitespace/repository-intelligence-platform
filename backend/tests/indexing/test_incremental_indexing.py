"""Incremental reindexing and .gitignore handling, against real ChromaDB.

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


def _index(
    root: Path,
    embedder: EmbeddingProvider,
    resolver: ProjectChromaStoreResolver,
) -> IndexingResult:
    return IndexingService(
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


def test_unchanged_repository_embeds_nothing_on_reindex(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    embedder = CountingEmbedder()

    first = _index(
        project,
        embedder,
        resolver,
    )

    embedded_first = len(
        embedder.embedded,
    )

    second = _index(
        project,
        embedder,
        resolver,
    )

    assert embedded_first > 0

    assert len(embedder.embedded) == embedded_first

    assert second.indexed_chunks == 0

    assert second.unchanged_files == 2

    assert second.indexed_files == first.indexed_files


def test_only_the_edited_file_is_re_embedded(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    embedder = CountingEmbedder()

    _index(
        project,
        embedder,
        resolver,
    )

    (project / "main.py").write_text(
        "def main():\n    return 'edited'\n",
        encoding="utf-8",
    )

    embedder.embedded.clear()

    result = _index(
        project,
        embedder,
        resolver,
    )

    assert embedder.embedded

    assert all("edited" in text for text in embedder.embedded)

    assert result.unchanged_files == 1

    # unchanged_files is part of indexed_files, so the counts add up to
    # scanned_files (an agent once added them and got one too many).
    assert result.unchanged_files <= result.indexed_files

    assert result.scanned_files == (
        result.indexed_files + result.skipped_files + result.failed_files
    )

    assert "Part of indexed_files" in (
        IndexingResult.model_json_schema()["properties"]["unchanged_files"]["description"]
    )

    # The old version of main.py is gone; search sees only current text.
    store = resolver.for_project(
        str(
            project.resolve(),
        ),
    )

    assert store is not None

    documents = store._collection.get()["documents"]  # noqa: SLF001

    assert any("edited" in document for document in documents)

    assert not any("'main'" in document for document in documents)


def test_deleted_file_is_removed_without_embedding_anything(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    embedder = CountingEmbedder()

    _index(
        project,
        embedder,
        resolver,
    )

    (project / "utils.py").unlink()

    embedder.embedded.clear()

    _index(
        project,
        embedder,
        resolver,
    )

    assert embedder.embedded == []

    assert _indexed_paths(project, resolver) == {
        "main.py",
    }


def test_switching_embedding_model_re_embeds_everything(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    _index(
        project,
        CountingEmbedder("fake:model-a"),
        resolver,
    )

    new_embedder = CountingEmbedder(
        "fake:model-b",
    )

    result = _index(
        project,
        new_embedder,
        resolver,
    )

    assert result.unchanged_files == 0

    assert {
        "main.py",
        "utils.py",
    } == _indexed_paths(
        project,
        resolver,
    )

    assert any("helper" in text for text in new_embedder.embedded)


def test_gitignored_files_are_not_indexed_and_are_dropped_when_ignored_later(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    (project / "dist").mkdir()

    (project / "dist" / "bundle.js").write_text(
        "function bundled() { return 1 }\n",
        encoding="utf-8",
    )

    (project / ".gitignore").write_text(
        "dist/\n",
        encoding="utf-8",
    )

    embedder = CountingEmbedder()

    _index(
        project,
        embedder,
        resolver,
    )

    assert "dist/bundle.js" not in _indexed_paths(
        project,
        resolver,
    )

    # Ignoring a file that is already indexed removes it on the next run.
    (project / ".gitignore").write_text(
        "dist/\nutils.py\n",
        encoding="utf-8",
    )

    _index(
        project,
        embedder,
        resolver,
    )

    paths = _indexed_paths(
        project,
        resolver,
    )

    assert "utils.py" not in paths

    assert "main.py" in paths


def test_lock_files_are_not_embedded(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    """Committed lock files are machine-written noise for semantic search."""

    (project / "package-lock.json").write_text(
        '{"lockfileVersion": 3}\n',
        encoding="utf-8",
    )

    (project / "uv.lock").write_text(
        "version = 1\n",
        encoding="utf-8",
    )

    result = _index(
        project,
        CountingEmbedder(),
        resolver,
    )

    paths = _indexed_paths(
        project,
        resolver,
    )

    assert "package-lock.json" not in paths

    assert "uv.lock" not in paths

    assert result.skipped_files >= 2


def test_a_file_that_fails_temporarily_keeps_its_index_entries(
    project: Path,
    resolver: ProjectChromaStoreResolver,
) -> None:
    """A locked or briefly unreadable file is not treated as deleted."""

    _index(
        project,
        CountingEmbedder(),
        resolver,
    )

    class FlakyLoader(RepositoryDocumentLoader):
        def load(self, entry):  # type: ignore[no-untyped-def]
            if entry.relative_path.name == "utils.py":
                raise OSError("file is locked")

            return super().load(entry)

    IndexingService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
        document_loader=FlakyLoader(),
        chunker=RepositoryChunker(),
        indexer=RepositoryIndexer(
            embedding_provider=CountingEmbedder(),
            vector_store_resolver=resolver,
        ),
    ).index_repository(
        project,
    )

    assert {
        "main.py",
        "utils.py",
    } <= _indexed_paths(
        project,
        resolver,
    )
