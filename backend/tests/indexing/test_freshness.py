"""Index freshness: hashes, updating given files, and the freshness service."""

import os
import threading
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from app.core.config.models import IndexingSettings
from app.core.config.provider import read_environment
from app.indexing import freshness
from app.indexing.freshness import (
    ChangeSet,
    FileHashCache,
    IndexFreshness,
    detect_changes,
)
from app.indexing.indexer import RepositoryIndexer
from app.indexing.lock import IndexingBusyError, project_index_lock
from app.indexing.models import EmbeddingVector, FreshnessResult, FreshnessState
from app.indexing.providers import EmbeddingProvider
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


def test_an_empty_file_is_not_counted_as_added(project, resolver):
    (project / ".pre-commit-config.yaml").write_bytes(b"")
    _index(project, CountingEmbedder(), resolver)

    assert _changes(project, resolver).total == 0


def test_whitespace_only_files_make_chunks_and_are_current(project, resolver):
    (project / "blank.txt").write_text("  \n\n", encoding="utf-8")
    _index(project, CountingEmbedder(), resolver)

    assert "blank.txt" in _indexed_paths(project, resolver)
    assert _changes(project, resolver).total == 0


def test_an_empty_python_file_is_indexed_and_current(project, resolver):
    (project / "__init__.py").write_bytes(b"")
    _index(project, CountingEmbedder(), resolver)

    assert "__init__.py" in _indexed_paths(project, resolver)
    assert _changes(project, resolver).total == 0


def test_the_no_chunk_rule_matches_the_chunker(tmp_path):
    from app.repository.chunking import RepositoryChunker, yields_no_chunks
    from app.repository.documents import RepositoryDocumentLoader

    contents = {
        "a.py": b"",
        "a.yaml": b"",
        "a.txt": b"",
        "b.txt": b"\n",
        "c.txt": b"  ",
        "c.py": b"  \n",
        "d.md": b"\n\n",
    }
    for name, data in contents.items():
        (tmp_path / name).write_bytes(data)

    for entry in RepositoryScanner().scan(tmp_path):
        RepositoryMetadataExtractor().enrich(entry)
        chunks = RepositoryChunker().chunk(RepositoryDocumentLoader().load(entry))

        assert yields_no_chunks(entry) == (not chunks), entry.name


def test_an_indexed_file_that_is_emptied_is_changed_then_removed(
    project, resolver, make_freshness
):
    (project / "notes.txt").write_text("some notes\n", encoding="utf-8")
    _index(project, CountingEmbedder(), resolver)
    (project / "notes.txt").write_bytes(b"")

    assert _changes(project, resolver).changed == ["notes.txt"]

    freshness_service = make_freshness(CountingEmbedder())

    assert freshness_service.refresh(project).state == FreshnessState.UPDATED
    assert "notes.txt" not in _indexed_paths(project, resolver)
    assert _changes(project, resolver).total == 0
    assert freshness_service.refresh(project).state == FreshnessState.UP_TO_DATE


def test_refresh_is_up_to_date_with_an_empty_file(project, resolver, make_freshness):
    (project / ".pre-commit-config.yaml").write_bytes(b"")
    _index(project, CountingEmbedder(), resolver)

    result = make_freshness(CountingEmbedder()).refresh(project)

    assert result.state == FreshnessState.UP_TO_DATE


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


# --- The freshness service -------------------------------------------------


class _Clock:
    """A fake monotonic clock; tests move it on events, never per call."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class _ScriptedEmbedder(CountingEmbedder):
    """Embeds like CountingEmbedder, with hooks the tests drive by events.

    - ``after_first`` runs once, after the first embed call (to move the clock).
    - ``fail_on`` makes any batch containing that text raise.
    - ``block`` (an Event) makes every call after the first wait for it
      (every call, with ``block_first``); ``blocked`` is set once one waits.
    """

    def __init__(self, identity: str = "fake:model-a") -> None:
        super().__init__(identity)
        self.after_first: Callable[[], None] | None = None
        self.fail_on: str | None = None
        self.block: threading.Event | None = None
        self.block_first = False
        self.blocked = threading.Event()
        self._calls = 0

    def embed(self, texts: Sequence[str]) -> list[EmbeddingVector]:
        if self.fail_on is not None and any(self.fail_on in text for text in texts):
            raise RuntimeError("provider down")
        self._calls += 1
        if self.block is not None and (self.block_first or self._calls > 1):
            self.blocked.set()
            assert self.block.wait(10), "test never released the embedder"
        vectors = super().embed(texts)
        if self._calls == 1 and self.after_first is not None:
            self.after_first()
        return vectors


@pytest.fixture
def make_freshness(project, resolver):
    """Build IndexFreshness over real services; joins background work after."""

    built: list[IndexFreshness] = []

    def build(
        embedder: EmbeddingProvider,
        refresh_seconds: int = 15,
        clock: Callable[[], float] | None = None,
    ) -> IndexFreshness:
        freshness_service = IndexFreshness(
            indexing_service=_service(embedder, resolver),
            scanner=RepositoryScanner(),
            metadata_extractor=RepositoryMetadataExtractor(),
            indexer=RepositoryIndexer(
                embedding_provider=embedder,
                vector_store_resolver=resolver,
            ),
            refresh_seconds=refresh_seconds,
            clock=clock or _Clock(),
        )
        built.append(freshness_service)
        return freshness_service

    yield build

    for freshness_service in built:
        assert freshness_service.wait_for_background(project, 10)


def _edit(project: Path, *names: str) -> None:
    for name in names:
        stem = name.removesuffix(".py")
        (project / name).write_text(
            f"def {stem}():\n    return 'changed'\n",
            encoding="utf-8",
        )


def _forbid_update_files(monkeypatch, freshness_service: IndexFreshness) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("update_files must not be called")

    monkeypatch.setattr(
        freshness_service._indexing_service,  # noqa: SLF001
        "update_files",
        fail,
    )


def test_up_to_date_does_nothing(project, resolver, make_freshness):
    _index(project, CountingEmbedder(), resolver)
    embedder = CountingEmbedder()

    result = make_freshness(embedder).refresh(project)

    assert result.state == FreshnessState.UP_TO_DATE
    assert result.note is None
    assert embedder.embedded == []


def test_changes_are_updated_before_returning(project, resolver, make_freshness):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py")
    (project / "utils.py").unlink()

    result = make_freshness(CountingEmbedder()).refresh(project)

    assert result.state == FreshnessState.UPDATED
    assert (result.changed_files, result.added_files, result.removed_files) == (1, 0, 1)
    assert result.updated_files == 2  # the edit and the removal
    assert result.pending_files == 0
    assert result.note is None
    assert _changes(project, resolver).total == 0


def test_past_the_limit_the_rest_finishes_in_the_background(
    project,
    resolver,
    make_freshness,
):
    (project / "other.py").write_text("X = 1\n", encoding="utf-8")
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py", "utils.py", "other.py")
    clock = _Clock()
    embedder = _ScriptedEmbedder()
    embedder.after_first = lambda: setattr(clock, "now", 99.0)
    freshness_service = make_freshness(embedder, refresh_seconds=1, clock=clock)

    result = freshness_service.refresh(project)

    assert result.state == FreshnessState.PARTIAL
    assert result.updated_files == 1
    assert result.pending_files == 2
    assert result.note == (
        "The index is still updating; 2 changed files are not included in this answer."
    )
    assert freshness_service.wait_for_background(project, 10) is True
    assert _changes(project, resolver).total == 0
    assert freshness_service.status(project).state == FreshnessState.UP_TO_DATE


def test_a_second_refresh_during_the_background_update_reports_partial(
    project,
    resolver,
    make_freshness,
    monkeypatch,
):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py", "utils.py")
    clock = _Clock()
    embedder = _ScriptedEmbedder()
    embedder.after_first = lambda: setattr(clock, "now", 99.0)
    embedder.block = threading.Event()  # holds the background update
    freshness_service = make_freshness(embedder, refresh_seconds=1, clock=clock)

    try:
        first = freshness_service.refresh(project)
        assert first.state == FreshnessState.PARTIAL
        assert embedder.blocked.wait(10)
        _forbid_update_files(monkeypatch, freshness_service)

        second = freshness_service.refresh(project)
        during = freshness_service.status(project)

    finally:
        embedder.block.set()

    assert second.state == FreshnessState.PARTIAL
    assert second.pending_files == 1
    assert second.updated_files == 0
    assert second.note == (
        "The index is still updating; 1 changed file is not included in this answer."
    )
    assert during.state == FreshnessState.UPDATING
    assert freshness_service.wait_for_background(project, 10) is True
    assert freshness_service.status(project).state == FreshnessState.UP_TO_DATE


def test_concurrent_refreshes_update_only_once(
    project,
    resolver,
    make_freshness,
    monkeypatch,
):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py")
    embedder = _ScriptedEmbedder()
    embedder.block = threading.Event()
    embedder.block_first = True  # holds the first refresh inside update_files
    freshness_service = make_freshness(embedder)
    results: list[FreshnessResult] = []
    first = threading.Thread(
        target=lambda: results.append(freshness_service.refresh(project)),
    )

    first.start()
    try:
        assert embedder.blocked.wait(10)
        _forbid_update_files(monkeypatch, freshness_service)

        second = freshness_service.refresh(project)

    finally:
        embedder.block.set()
        first.join(10)

    assert not first.is_alive()
    assert second.state == FreshnessState.PARTIAL
    assert second.pending_files == 1
    assert [result.state for result in results] == [FreshnessState.UPDATED]


def test_busy_lock_answers_without_waiting(project, resolver, make_freshness):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py", "utils.py")
    embedder = CountingEmbedder()
    freshness_service = make_freshness(embedder)

    with project_index_lock(project.resolve()):
        result = freshness_service.refresh(project)
        during = freshness_service.status(project)

    assert result.state == FreshnessState.BUSY
    assert result.pending_files == 2
    assert result.note == (
        "Another index update is running; 2 changed files may not be "
        "included in this answer."
    )
    assert embedder.embedded == []
    assert during.state == FreshnessState.STALE  # no background thread here


def test_off_reports_the_change_set_only(project, resolver, make_freshness, monkeypatch):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py")
    embedder = CountingEmbedder()
    freshness_service = make_freshness(embedder, refresh_seconds=0)
    _forbid_update_files(monkeypatch, freshness_service)

    result = freshness_service.refresh(project)

    assert result.state == FreshnessState.OFF
    assert result.changed_files == 1
    assert result.pending_files == 1
    assert result.note == (
        "Automatic index updates are off; 1 file changed since indexing is not included."
    )
    assert embedder.embedded == []
    assert freshness_service.status(project).state == FreshnessState.OFF


def test_not_indexed_and_incompatible_do_nothing(
    project,
    resolver,
    make_freshness,
    monkeypatch,
):
    embedder = CountingEmbedder()
    unindexed = make_freshness(embedder)
    _forbid_update_files(monkeypatch, unindexed)

    assert unindexed.refresh(project).state == FreshnessState.NOT_INDEXED
    assert unindexed.status(project).state == FreshnessState.NOT_INDEXED
    assert unindexed.changes(project) is None

    _index(project, CountingEmbedder("fake:model-a"), resolver)
    _edit(project, "main.py")
    other_model = CountingEmbedder("fake:model-b")
    incompatible = make_freshness(other_model)
    _forbid_update_files(monkeypatch, incompatible)

    assert incompatible.refresh(project).state == FreshnessState.INCOMPATIBLE
    assert incompatible.status(project).state == FreshnessState.INCOMPATIBLE
    assert incompatible.changes(project) is None
    assert other_model.embedded == []
    assert embedder.embedded == []


def test_a_file_that_fails_to_embed_stays_pending(project, resolver, make_freshness):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py")
    embedder = _ScriptedEmbedder()
    embedder.fail_on = "changed"
    freshness_service = make_freshness(embedder)

    result = freshness_service.refresh(project)

    assert result.state == FreshnessState.PARTIAL
    assert result.updated_files == 0
    assert result.pending_files == 1
    assert result.note == (
        "The index is still updating; 1 changed file is not included in this answer."
    )
    contents = _contents(project, resolver, "main.py")
    assert contents and all("'main'" in content for content in contents)
    # Failed files get no background update: nothing is running.
    assert freshness_service.status(project).state == FreshnessState.STALE

    embedder.fail_on = None
    retried = freshness_service.refresh(project)

    assert retried.state == FreshnessState.UPDATED
    assert retried.updated_files == 1
    assert _changes(project, resolver).total == 0


def test_an_unexpected_error_becomes_the_failure_note(
    project,
    resolver,
    make_freshness,
    monkeypatch,
    caplog,
):
    _index(project, CountingEmbedder(), resolver)

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(freshness, "detect_changes", boom)

    with caplog.at_level("ERROR"):
        result = make_freshness(CountingEmbedder()).refresh(project)

    assert result.state == FreshnessState.FAILED
    assert result.note == (
        "The index could not be updated (boom); 0 changed files may not be "
        "included in this answer."
    )
    assert "boom" in caplog.text


def test_changes_never_raises(
    project,
    resolver,
    make_freshness,
    monkeypatch,
    caplog,
):
    _index(project, CountingEmbedder(), resolver)

    def boom(*args, **kwargs):
        raise RuntimeError("detection broke")

    monkeypatch.setattr(freshness, "detect_changes", boom)

    with caplog.at_level("ERROR"):
        result = make_freshness(CountingEmbedder()).changes(project)

    assert result is None
    assert "detection broke" in caplog.text


def test_an_error_while_updating_counts_the_known_changes(
    project,
    resolver,
    make_freshness,
    monkeypatch,
):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py", "utils.py")
    freshness_service = make_freshness(CountingEmbedder())

    def broken(*args, **kwargs):
        raise RuntimeError("store unavailable")

    monkeypatch.setattr(
        freshness_service._indexing_service,  # noqa: SLF001
        "update_files",
        broken,
    )

    result = freshness_service.refresh(project)

    assert result.state == FreshnessState.FAILED
    assert result.note == (
        "The index could not be updated (store unavailable); 2 changed files may "
        "not be included in this answer."
    )
    # The claim is released: a later refresh tries again.
    monkeypatch.undo()
    assert freshness_service.refresh(project).state == FreshnessState.UPDATED


def test_a_failing_background_update_is_logged_and_released(
    project,
    resolver,
    make_freshness,
    monkeypatch,
    caplog,
):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py", "utils.py")
    clock = _Clock()
    embedder = _ScriptedEmbedder()
    embedder.after_first = lambda: setattr(clock, "now", 99.0)
    freshness_service = make_freshness(embedder, refresh_seconds=1, clock=clock)
    service = freshness_service._indexing_service  # noqa: SLF001
    real = service.update_files

    def foreground_only(root, to_index, to_remove, deadline=None, **kwargs):
        if deadline is None:
            raise RuntimeError("background broke")
        return real(root, to_index, to_remove, deadline=deadline, **kwargs)

    monkeypatch.setattr(service, "update_files", foreground_only)

    with caplog.at_level("ERROR"):
        assert freshness_service.refresh(project).state == FreshnessState.PARTIAL
        assert freshness_service.wait_for_background(project, 10) is True

    assert "background broke" in caplog.text
    assert freshness_service.status(project).state == FreshnessState.STALE


def test_a_busy_background_update_stops_quietly(
    project,
    resolver,
    make_freshness,
    monkeypatch,
    caplog,
):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py", "utils.py")
    clock = _Clock()
    embedder = _ScriptedEmbedder()
    embedder.after_first = lambda: setattr(clock, "now", 99.0)
    freshness_service = make_freshness(embedder, refresh_seconds=1, clock=clock)
    service = freshness_service._indexing_service  # noqa: SLF001
    real = service.update_files

    def busy_in_background(root, to_index, to_remove, deadline=None, **kwargs):
        if deadline is None:
            raise IndexingBusyError("another process")
        return real(root, to_index, to_remove, deadline=deadline, **kwargs)

    monkeypatch.setattr(service, "update_files", busy_in_background)

    with caplog.at_level("ERROR"):
        assert freshness_service.refresh(project).state == FreshnessState.PARTIAL
        assert freshness_service.wait_for_background(project, 10) is True

    assert caplog.records == []
    assert freshness_service.status(project).state == FreshnessState.STALE


def test_status_never_updates(project, resolver, make_freshness):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py")
    embedder = CountingEmbedder()

    result = make_freshness(embedder).status(project)

    assert result.state == FreshnessState.STALE
    assert result.changed_files == 1
    assert result.pending_files == 1
    assert embedder.embedded == []
    assert _changes(project, resolver).total == 1


def test_the_hash_cache_forgets_files_that_are_gone(project, resolver):
    _index(project, CountingEmbedder(), resolver)
    cache = FileHashCache()
    _changes(project, resolver, cache)
    (project / "utils.py").unlink()

    _changes(project, resolver, cache)

    assert [path.name for path in cache._entries] == ["main.py"]  # noqa: SLF001


def test_refresh_seconds_setting(monkeypatch):
    for name in ("RIP_INDEXING_REFRESH_SECONDS", "LOC_INDEXING_REFRESH_SECONDS"):
        monkeypatch.delenv(name, raising=False)

    assert read_environment(env_file=None).indexing_refresh_seconds == 15
    assert IndexingSettings().refresh_seconds == 15

    monkeypatch.setenv("RIP_INDEXING_REFRESH_SECONDS", "7")

    assert read_environment(env_file=None).indexing_refresh_seconds == 7


# --- A model change during an update (Ruling 19) ----------------------------


def _built_with(project: Path, resolver: ProjectChromaStoreResolver) -> str | None:
    return RepositoryIndexer(
        embedding_provider=CountingEmbedder(),
        vector_store_resolver=resolver,
    ).status(str(project.resolve())).embedding_model


def test_update_files_stops_between_files_when_the_model_changes(
    project,
    resolver,
    monkeypatch,
):
    _index(project, CountingEmbedder("fake:model-a"), resolver)
    _edit(project, "main.py", "utils.py")
    embedder = CountingEmbedder("fake:model-a")
    service = _service(embedder, resolver)
    indexer = service._indexer  # noqa: SLF001
    finish_file = indexer.remove_chunks_of_path_except

    def finish_then_switch(*args, **kwargs):
        removed = finish_file(*args, **kwargs)
        embedder._identity = "fake:model-b"  # noqa: SLF001
        return removed

    monkeypatch.setattr(indexer, "remove_chunks_of_path_except", finish_then_switch)

    result = service.update_files(project, ["main.py", "utils.py"], [])

    assert result.done == ["main.py"]
    assert result.remaining == ["utils.py"]
    assert result.model_changed is True
    assert _built_with(project, resolver) == "fake:model-a"
    assert all("'helper'" in content for content in _contents(project, resolver, "utils.py"))


def test_a_file_embedded_after_the_model_changed_is_not_written(project, resolver):
    _index(project, CountingEmbedder("fake:model-a"), resolver)
    _edit(project, "main.py", "utils.py")
    embedder = _ScriptedEmbedder("fake:model-a")
    # The lazy provider would embed this batch with the new model.
    embedder.after_first = lambda: setattr(embedder, "_identity", "fake:model-b")

    result = _service(embedder, resolver).update_files(project, ["main.py", "utils.py"], [])

    assert result.done == []
    assert result.remaining == ["main.py", "utils.py"]
    assert result.model_changed is True
    assert _built_with(project, resolver) == "fake:model-a"
    assert all("'main'" in content for content in _contents(project, resolver, "main.py"))


def test_a_model_change_mid_update_leaves_the_rest_and_reports_incompatible(
    project,
    resolver,
    make_freshness,
    monkeypatch,
):
    _index(project, CountingEmbedder("fake:model-a"), resolver)
    _edit(project, "main.py", "utils.py")
    embedder = _ScriptedEmbedder("fake:model-a")
    embedder.after_first = lambda: setattr(embedder, "_identity", "fake:model-b")
    freshness_service = make_freshness(embedder)

    result = freshness_service.refresh(project)

    assert result.state == FreshnessState.INCOMPATIBLE
    assert result.pending_files == 2
    assert result.note is None
    assert freshness_service._background == {}  # noqa: SLF001 - no background update
    assert _built_with(project, resolver) == "fake:model-a"

    _forbid_update_files(monkeypatch, freshness_service)

    assert freshness_service.refresh(project).state == FreshnessState.INCOMPATIBLE
    assert freshness_service.status(project).state == FreshnessState.INCOMPATIBLE


# --- Files that always fail (Ruling 20) --------------------------------------


def _write_latin1(project: Path, name: str = "notes.txt") -> None:
    (project / name).write_bytes("caf\xe9 au lait\n".encode("latin-1"))


def test_update_files_tells_content_failures_from_other_failures(
    project,
    resolver,
    monkeypatch,
):
    _index(project, CountingEmbedder(), resolver)
    _write_latin1(project)
    _edit(project, "main.py")
    service = _service(CountingEmbedder(), resolver)
    loader = service._document_loader  # noqa: SLF001
    load = loader.load

    def locked_main(entry):
        if entry.name == "main.py":
            raise PermissionError("locked by another program")
        return load(entry)

    monkeypatch.setattr(loader, "load", locked_main)

    result = service.update_files(project, ["notes.txt", "main.py"], [])

    assert result.unindexable == ["notes.txt"]
    assert result.failed == ["main.py"]
    assert result.done == []


def test_a_file_whose_content_cannot_be_indexed_is_left_out_until_it_changes(
    project,
    resolver,
    make_freshness,
    monkeypatch,
    caplog,
):
    _index(project, CountingEmbedder(), resolver)
    _write_latin1(project)
    freshness_service = make_freshness(CountingEmbedder())

    with caplog.at_level("WARNING", logger="app.indexing.freshness"):
        first = freshness_service.refresh(project)

        assert first.state == FreshnessState.UPDATED
        assert first.pending_files == 0
        assert first.note is None

        update_files = freshness_service._indexing_service.update_files  # noqa: SLF001
        _forbid_update_files(monkeypatch, freshness_service)

        second = freshness_service.refresh(project)
        status = freshness_service.status(project)

    assert second.state == FreshnessState.UP_TO_DATE
    assert second.note is None
    assert status.state == FreshnessState.UP_TO_DATE
    remembered = [
        record for record in caplog.records
        if record.name == "app.indexing.freshness" and "notes.txt" in record.getMessage()
    ]
    assert len(remembered) == 1

    # Fixed content is tried again.
    monkeypatch.setattr(
        freshness_service._indexing_service,  # noqa: SLF001
        "update_files",
        update_files,
    )
    (project / "notes.txt").write_text("cafe au lait\n", encoding="utf-8")

    fixed = freshness_service.refresh(project)

    assert fixed.state == FreshnessState.UPDATED
    assert fixed.updated_files == 1
    assert "notes.txt" in _indexed_paths(project, resolver)


def test_a_provider_failure_is_retried_on_every_refresh(project, resolver, make_freshness):
    _index(project, CountingEmbedder(), resolver)
    _edit(project, "main.py")
    embedder = _ScriptedEmbedder()
    embedder.fail_on = "changed"
    attempts: list[int] = []
    freshness_service = make_freshness(embedder)
    update_files = freshness_service._indexing_service.update_files  # noqa: SLF001

    def counted(*args, **kwargs):
        attempts.append(1)
        return update_files(*args, **kwargs)

    freshness_service._indexing_service.update_files = counted  # noqa: SLF001

    first = freshness_service.refresh(project)
    second = freshness_service.refresh(project)

    assert [first.state, second.state] == [FreshnessState.PARTIAL, FreshnessState.PARTIAL]
    assert second.pending_files == 1
    assert len(attempts) == 2
    assert freshness_service.status(project).state == FreshnessState.STALE


def test_notes_use_one_file_and_n_files():
    assert freshness.partial_note(1) == (
        "The index is still updating; 1 changed file is not included in this answer."
    )
    assert freshness.partial_note(3) == (
        "The index is still updating; 3 changed files are not included in this answer."
    )
    assert freshness.busy_note(1) == (
        "Another index update is running; 1 changed file may not be included in "
        "this answer."
    )
    assert freshness.off_note(2) == (
        "Automatic index updates are off; 2 files changed since indexing are not "
        "included."
    )
    assert freshness.failure_note(RuntimeError("boom"), 1) == (
        "The index could not be updated (boom); 1 changed file may not be included "
        "in this answer."
    )
