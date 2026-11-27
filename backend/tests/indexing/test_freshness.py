"""Index freshness: per-file hashes and updating a given set of files."""

import os
from collections.abc import Sequence
from pathlib import Path

import pytest

from app.indexing import freshness
from app.indexing.freshness import ChangeSet, FileHashCache, detect_changes
from app.indexing.indexer import RepositoryIndexer
from app.indexing.lock import IndexingBusyError, project_index_lock
from app.indexing.models import EmbeddingVector
from app.indexing.store_resolver import ProjectChromaStoreResolver
from app.repository.hashing import calculate_sha256
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner
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


def _changes(
    project: Path,
    resolver: ProjectChromaStoreResolver,
    cache: FileHashCache | None = None,
) -> ChangeSet:
    return detect_changes(
        project.resolve(),
        RepositoryScanner(),
        RepositoryMetadataExtractor(),
        RepositoryIndexer(
            embedding_provider=CountingEmbedder(),
            vector_store_resolver=resolver,
        ),
        cache or FileHashCache(),
    )


def test_nothing_changed_right_after_indexing(project, resolver):
    (project / "pkg").mkdir()
    (project / "pkg" / "deep.py").write_text("X = 1\n", encoding="utf-8")

    _index(project, CountingEmbedder(), resolver)

    assert _changes(project, resolver).total == 0


def test_edit_add_and_delete_are_reported(project, resolver):
    _index(project, CountingEmbedder(), resolver)

    (project / "main.py").write_text("changed\n", encoding="utf-8")
    (project / "new.py").write_text("new\n", encoding="utf-8")
    (project / "utils.py").unlink()

    changes = _changes(project, resolver)

    assert (changes.changed, changes.added, changes.removed) == (
        ["main.py"],
        ["new.py"],
        ["utils.py"],
    )


def test_an_edit_that_is_undone_counts_as_unchanged(project, resolver):
    _index(project, CountingEmbedder(), resolver)

    original = (project / "main.py").read_text(encoding="utf-8")
    (project / "main.py").write_text("changed\n", encoding="utf-8")
    (project / "main.py").write_text(original, encoding="utf-8")

    assert _changes(project, resolver).total == 0


def test_a_newly_ignored_file_is_removed(project, resolver):
    _index(project, CountingEmbedder(), resolver)

    (project / ".gitignore").write_text("utils.py\n", encoding="utf-8")

    changes = _changes(project, resolver)

    assert changes.removed == ["utils.py"]
    assert changes.changed == []


def test_a_file_that_is_no_longer_text_is_removed(
    project,
    resolver,
    monkeypatch,
):
    _index(project, CountingEmbedder(), resolver)

    real = RepositoryMetadataExtractor.enrich_fast

    def not_text(self, entry):
        entry = real(self, entry)
        if entry.name == "utils.py":
            entry.is_text_file = False
        return entry

    monkeypatch.setattr(RepositoryMetadataExtractor, "enrich_fast", not_text)

    changes = _changes(project, resolver)

    assert changes.removed == ["utils.py"]
    assert changes.changed == []


def test_a_file_that_vanishes_while_hashing_is_removed(
    project,
    resolver,
    monkeypatch,
):
    _index(project, CountingEmbedder(), resolver)

    real = FileHashCache.sha256

    def vanishing(self, path):
        if path.name == "utils.py":
            raise FileNotFoundError(str(path))
        return real(self, path)

    monkeypatch.setattr(FileHashCache, "sha256", vanishing)

    changes = _changes(project, resolver)

    assert changes.removed == ["utils.py"]
    assert changes.total == 1


def test_a_new_file_that_vanishes_while_hashing_is_ignored(
    project,
    resolver,
    monkeypatch,
):
    _index(project, CountingEmbedder(), resolver)

    (project / "new.py").write_text("new\n", encoding="utf-8")

    real = FileHashCache.sha256

    def vanishing(self, path):
        if path.name == "new.py":
            raise FileNotFoundError(str(path))
        return real(self, path)

    monkeypatch.setattr(FileHashCache, "sha256", vanishing)

    assert _changes(project, resolver).total == 0


def test_unchanged_files_are_not_read_again(project, resolver, monkeypatch):
    _index(project, CountingEmbedder(), resolver)

    calls: list[Path] = []
    real = freshness.calculate_sha256

    def counting(path):
        calls.append(path)
        return real(path)

    monkeypatch.setattr(freshness, "calculate_sha256", counting)

    cache = FileHashCache()

    _changes(project, resolver, cache)
    first = len(calls)
    _changes(project, resolver, cache)

    assert first == 2
    assert len(calls) == first


def test_to_index_lists_the_most_recently_modified_first(project, resolver):
    _index(project, CountingEmbedder(), resolver)

    (project / "main.py").write_text("changed\n", encoding="utf-8")
    (project / "new.py").write_text("new\n", encoding="utf-8")
    (project / "utils.py").write_text("changed too\n", encoding="utf-8")

    os.utime(project / "main.py", (1_000_000, 1_000_000))
    os.utime(project / "new.py", (3_000_000, 3_000_000))
    os.utime(project / "utils.py", (2_000_000, 2_000_000))

    assert _changes(project, resolver).to_index == [
        "new.py",
        "utils.py",
        "main.py",
    ]
