"""Index freshness: per-file hashes and updating a given set of files."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from app.indexing.indexer import RepositoryIndexer
from app.indexing.lock import IndexingBusyError, project_index_lock
from app.indexing.models import EmbeddingVector
from app.indexing.store_resolver import ProjectChromaStoreResolver
from app.repository.hashing import calculate_sha256
from tests.indexing.conftest import (
    CountingEmbedder,
    _index,
    _indexed_paths,
    _service,
)


def _contents(
    root: Path,
    resolver: ProjectChromaStoreResolver,
    relative_path: str,
) -> list[str]:
    store = resolver.for_project(str(root.resolve()))

    assert store is not None

    result = store._collection.get(  # noqa: SLF001
        include=["documents", "metadatas"],
    )

    return [
        document
        for document, metadata in zip(result["documents"], result["metadatas"])
        if Path(metadata["relative_path"]).as_posix() == relative_path
    ]


def test_indexed_file_hashes_match_the_files(project, resolver):
    _index(project, CountingEmbedder(), resolver)
    indexer = RepositoryIndexer(
        embedding_provider=CountingEmbedder(),
        vector_store_resolver=resolver,
    )

    hashes = indexer.indexed_file_hashes(str(project.resolve()))

    assert set(hashes) == {"main.py", "utils.py"}
    assert hashes["main.py"] == calculate_sha256(project / "main.py")


def test_update_files_embeds_only_the_edited_file(project, resolver):
    _index(project, CountingEmbedder(), resolver)
    (project / "main.py").write_text("def main():\n    return 'changed'\n", encoding="utf-8")
    embedder = CountingEmbedder()

    result = _service(embedder, resolver).update_files(project, ["main.py"], [])

    assert result.done == ["main.py"] and result.remaining == []
    assert embedder.embedded
    assert all("changed" in text for text in embedder.embedded)
    assert not any("helper" in text for text in embedder.embedded)
    contents = _contents(project, resolver, "main.py")
    assert contents
    assert all("changed" in content for content in contents)  # old chunk gone
    assert _indexed_paths(project, resolver) == {"main.py", "utils.py"}


def test_update_files_removes_deleted_files(project, resolver):
    _index(project, CountingEmbedder(), resolver)
    (project / "utils.py").unlink()
    embedder = CountingEmbedder()

    result = _service(embedder, resolver).update_files(project, [], ["utils.py"])

    assert result.failed == []
    assert embedder.embedded == []
    assert _indexed_paths(project, resolver) == {"main.py"}


def test_update_files_treats_a_vanished_file_as_removed(project, resolver):
    _index(project, CountingEmbedder(), resolver)
    (project / "utils.py").unlink()

    result = _service(CountingEmbedder(), resolver).update_files(project, ["utils.py"], [])

    assert result.done == ["utils.py"]
    assert _indexed_paths(project, resolver) == {"main.py"}


def test_update_files_stops_starting_files_at_the_deadline(project, resolver):
    now = [0.0]

    class SlowEmbedder(CountingEmbedder):
        def embed(self, texts: Sequence[str]) -> list[EmbeddingVector]:
            vectors = super().embed(texts)
            now[0] = 99.0  # embedding the first file used up the budget
            return vectors

    result = _service(SlowEmbedder(), resolver).update_files(
        project,
        ["main.py", "utils.py"],
        [],
        deadline=10.0,
        clock=lambda: now[0],
    )

    assert result.done == ["main.py"]
    assert result.remaining == ["utils.py"]
    assert _indexed_paths(project, resolver) == {"main.py"}


def test_a_file_that_fails_keeps_its_chunks(project, resolver):
    _index(project, CountingEmbedder(), resolver)
    (project / "main.py").write_text("def main():\n    return 'changed'\n", encoding="utf-8")

    class FailingEmbedder(CountingEmbedder):
        def embed(self, texts: Sequence[str]) -> list[EmbeddingVector]:
            if any("changed" in text for text in texts):
                raise RuntimeError("provider down")
            return super().embed(texts)

    result = _service(FailingEmbedder(), resolver).update_files(project, ["main.py"], [])

    assert result.failed == ["main.py"]
    assert result.done == []
    contents = _contents(project, resolver, "main.py")
    assert contents
    assert all("'main'" in content for content in contents)


def test_update_files_raises_when_the_index_lock_is_held(project, resolver):
    with project_index_lock(project.resolve()):
        with pytest.raises(IndexingBusyError):
            _service(CountingEmbedder(), resolver).update_files(project, ["main.py"], [])
