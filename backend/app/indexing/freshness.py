"""Keep a project's semantic index in step with its files.

``detect_changes`` finds the files that differ from the index;
``IndexFreshness`` updates them before an answer, up to a time limit,
and finishes the rest in a background thread.
"""

import logging
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from app.indexing.exceptions import IndexingBusyError
from app.indexing.indexer import RepositoryIndexer
from app.indexing.models import FreshnessResult, FreshnessState
from app.indexing.service import IndexingService
from app.repository.hashing import calculate_sha256
from app.repository.ignore import is_indexable_file_name
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner

logger = logging.getLogger(__name__)

PARTIAL_NOTE = (
    "The index is still updating; {n} changed files are not included in "
    "this answer."
)

BUSY_NOTE = (
    "Another RIP process is updating the index; {n} changed files may not "
    "be included in this answer."
)

OFF_NOTE = (
    "Automatic index updates are off; {n} files changed since indexing are "
    "not included."
)

FAILURE_NOTE = (
    "The index could not be updated ({error}); {n} changed files may not be "
    "included in this answer."
)


@dataclass(frozen=True)
class ChangeSet:
    """Files that differ from the index, in the stored path form."""

    changed: list[str] = field(default_factory=list)

    added: list[str] = field(default_factory=list)

    removed: list[str] = field(default_factory=list)

    modified_ns: dict[str, int] = field(
        default_factory=dict,
        compare=False,
        repr=False,
    )

    @property
    def to_index(self) -> list[str]:
        """Files to (re-)index, most recently modified first."""

        return sorted(
            [*self.changed, *self.added],
            key=lambda path: self.modified_ns.get(path, 0),
            reverse=True,
        )

    @property
    def total(self) -> int:
        return len(self.changed) + len(self.added) + len(self.removed)


class FileHashCache:
    """SHA-256 per file, reused while its mtime and size are unchanged.

    Safe to share between threads.
    """

    def __init__(self) -> None:
        self._entries: dict[Path, tuple[int, int, str]] = {}

        self._lock = threading.Lock()

    def sha256(self, path: Path) -> str:
        """Hash a file; raises ``OSError`` if it is gone or unreadable."""

        stat = path.stat()

        with self._lock:
            cached = self._entries.get(path)

        if cached is not None and cached[:2] == (stat.st_mtime_ns, stat.st_size):
            return cached[2]

        digest = calculate_sha256(path)

        with self._lock:
            self._entries[path] = (stat.st_mtime_ns, stat.st_size, digest)

        return digest

    def forget_unseen(
        self,
        root_directory: Path,
        seen: Iterable[Path],
    ) -> None:
        """Drop entries under ``root_directory`` that are not in ``seen``."""

        keep = set(seen)

        with self._lock:
            self._entries = {
                path: entry
                for path, entry in self._entries.items()
                if path in keep or not path.is_relative_to(root_directory)
            }


def detect_changes(
    root_directory: Path,
    scanner: RepositoryScanner,
    metadata_extractor: RepositoryMetadataExtractor,
    indexer: RepositoryIndexer,
    cache: FileHashCache,
) -> ChangeSet:
    """Compare the files on disk with what the index holds.

    "Current" files are the ones indexing would index: not directories,
    indexable by name, and text. A file that vanishes mid-scan counts as
    removed if it was indexed, and is ignored otherwise. Cache entries for
    files under the root that this scan did not hash are dropped.
    """

    root_directory = root_directory.resolve()

    indexed = indexer.indexed_file_hashes(
        str(root_directory),
    )

    changed: list[str] = []

    added: list[str] = []

    modified_ns: dict[str, int] = {}

    seen: set[str] = set()

    hashed: list[Path] = []

    for entry in scanner.scan(root_directory):
        if entry.is_directory or not is_indexable_file_name(entry.name):
            continue

        relative_path = str(entry.relative_path)

        try:
            metadata_extractor.enrich_fast(entry)

            if not entry.is_text_file:
                continue

            digest = cache.sha256(entry.absolute_path)

            hashed.append(entry.absolute_path)

            modified_ns[relative_path] = entry.absolute_path.stat().st_mtime_ns

        except OSError:
            continue

        seen.add(relative_path)

        stored = indexed.get(relative_path)

        if stored is None:
            added.append(relative_path)

        elif stored != digest:
            changed.append(relative_path)

    cache.forget_unseen(root_directory, hashed)

    return ChangeSet(
        changed=changed,
        added=added,
        removed=sorted(set(indexed) - seen),
        modified_ns=modified_ns,
    )


class IndexFreshness:
    """Update a project's changed files before an answer, up to a limit.

    One instance serves the whole process. Per resolved project root it
    keeps a hash cache and a claim: at most one update (an answer's, or
    the background one that finishes it) runs for a root in this process.
    A ``refresh`` that finds the root claimed does not touch the index
    lock and reports ``partial``. Other processes are kept out by the
    index lock, which ``update_files`` takes without waiting (``busy``).

    ``refresh`` and ``status`` never raise: a failure is logged and
    returned as a note. An unindexed project, or an index built with a
    different embedding model, is never updated.
    """

    def __init__(
        self,
        indexing_service: IndexingService,
        scanner: RepositoryScanner,
        metadata_extractor: RepositoryMetadataExtractor,
        indexer: RepositoryIndexer,
        refresh_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._indexing_service = indexing_service
        self._scanner = scanner
        self._metadata_extractor = metadata_extractor
        self._indexer = indexer
        self._refresh_seconds = refresh_seconds
        self._clock = clock

        # Guards the three collections below; never held during I/O.
        self._lock = threading.Lock()
        self._caches: dict[Path, FileHashCache] = {}
        self._claimed: set[Path] = set()
        self._background: dict[Path, threading.Thread] = {}

    def changes(
        self,
        root_directory: Path,
    ) -> ChangeSet | None:
        """Files that differ from the index; None if not indexed or incompatible."""

        root_directory = root_directory.resolve()

        if self._skip_state(root_directory) is not None:
            return None

        return self._detect(root_directory)

    def refresh(
        self,
        root_directory: Path,
        changes: ChangeSet | None = None,
    ) -> FreshnessResult:
        """Update changed files, spending at most ``refresh_seconds``.

        ``changes`` saves detecting them again when the caller already
        has them (from ``changes``). Removed files go first, then the most
        recently modified. Files the limit left are finished by a
        background update; files that failed stay pending until the next
        ``refresh``.
        """

        started = self._clock()

        root_directory = root_directory.resolve()

        try:
            # Checked even when the caller passes changes: the model may
            # have changed since, and update_files never rebuilds an index.
            skipped = self._skip_state(root_directory)

            if skipped is not None:
                return self._result(skipped, None, started)

            if changes is None:
                changes = self._detect(root_directory)

            return self._update(
                root_directory,
                changes,
                started,
            )

        except Exception as exc:
            logger.exception(
                "Could not update the index for %s",
                root_directory,
            )

            return self._failure(
                exc,
                changes,
                started,
            )

    def status(
        self,
        root_directory: Path,
    ) -> FreshnessResult:
        """The state and counts ``refresh`` would start from; updates nothing.

        ``updating`` while this process updates the root, ``stale`` when
        files changed and nothing here is updating them.
        """

        started = self._clock()

        root_directory = root_directory.resolve()

        try:
            skipped = self._skip_state(root_directory)

            if skipped is not None:
                return self._result(skipped, None, started)

            changes = self._detect(root_directory)

            with self._lock:
                updating = root_directory in self._claimed

            if updating:
                state = FreshnessState.UPDATING

            elif changes.total == 0:
                state = FreshnessState.UP_TO_DATE

            elif self._refresh_seconds <= 0:
                return self._off(changes, started)

            else:
                state = FreshnessState.STALE

            return self._result(
                state,
                changes,
                started,
                pending=changes.total,
            )

        except Exception as exc:
            logger.exception(
                "Could not read the index state for %s",
                root_directory,
            )

            return self._failure(
                exc,
                None,
                started,
            )

    def wait_for_background(
        self,
        root_directory: Path,
        timeout: float,
    ) -> bool:
        """Wait for this process's background update of a root to end.

        True when none is running any more. For tests and measurements.
        """

        with self._lock:
            thread = self._background.get(
                root_directory.resolve(),
            )

        if thread is None:
            return True

        thread.join(
            timeout,
        )

        return not thread.is_alive()

    def _update(
        self,
        root_directory: Path,
        changes: ChangeSet,
        started: float,
    ) -> FreshnessResult:
        if changes.total == 0:
            return self._result(FreshnessState.UP_TO_DATE, changes, started)

        if self._refresh_seconds <= 0:
            return self._off(changes, started)

        with self._lock:
            already_updating = root_directory in self._claimed

            self._claimed.add(root_directory)

        if already_updating:
            return self._result(
                FreshnessState.PARTIAL,
                changes,
                started,
                pending=changes.total,
                note=PARTIAL_NOTE.format(n=changes.total),
            )

        handed_off = False

        try:
            try:
                update = self._indexing_service.update_files(
                    root_directory,
                    changes.to_index,
                    changes.removed,
                    deadline=self._clock() + self._refresh_seconds,
                    clock=self._clock,
                )

            except IndexingBusyError:
                return self._result(
                    FreshnessState.BUSY,
                    changes,
                    started,
                    pending=changes.total,
                    note=BUSY_NOTE.format(n=changes.total),
                )

            if update.remaining:
                self._start_background(
                    root_directory,
                    update.remaining,
                )

                handed_off = True

        finally:
            if not handed_off:
                with self._lock:
                    self._claimed.discard(root_directory)

        pending = len(update.remaining) + len(update.failed)

        return self._result(
            FreshnessState.PARTIAL if pending else FreshnessState.UPDATED,
            changes,
            started,
            updated=len(update.done) + len(changes.removed),
            pending=pending,
            note=PARTIAL_NOTE.format(n=pending) if pending else None,
        )

    def _start_background(
        self,
        root_directory: Path,
        files: list[str],
    ) -> None:
        """Hand this root's claim to a thread that finishes ``files``.

        Registered before it starts, so ``wait_for_background`` sees it
        and the thread's own cleanup always finds its entry.
        """

        thread = threading.Thread(
            target=self._finish_in_background,
            args=(root_directory, files),
            name=f"rip-index-refresh:{root_directory.name}",
            daemon=True,
        )

        with self._lock:
            self._background[root_directory] = thread

        try:
            thread.start()

        except BaseException:
            with self._lock:
                self._background.pop(root_directory, None)

            raise

    def _finish_in_background(
        self,
        root_directory: Path,
        files: list[str],
    ) -> None:
        """Update ``files`` with no deadline, then release the claim; never raises."""

        try:
            update = self._indexing_service.update_files(
                root_directory,
                files,
                [],
                deadline=None,
            )

            logger.info(
                "Finished updating the index for %s in the background: "
                "%d files updated, %d failed",
                root_directory,
                len(update.done),
                len(update.failed),
            )

        except IndexingBusyError:
            # Another process started indexing; it brings these files in.
            logger.info(
                "Background index update for %s stopped: another process "
                "is indexing",
                root_directory,
            )

        except Exception:
            logger.exception(
                "Background index update for %s failed",
                root_directory,
            )

        finally:
            with self._lock:
                self._claimed.discard(root_directory)

                self._background.pop(root_directory, None)

    def _skip_state(
        self,
        root_directory: Path,
    ) -> FreshnessState | None:
        """``not_indexed`` or ``incompatible`` when freshness must not act."""

        index_status = self._indexer.status(
            str(root_directory),
        )

        if not index_status.indexed:
            return FreshnessState.NOT_INDEXED

        if not index_status.compatible:
            return FreshnessState.INCOMPATIBLE

        return None

    def _detect(
        self,
        root_directory: Path,
    ) -> ChangeSet:
        with self._lock:
            cache = self._caches.setdefault(
                root_directory,
                FileHashCache(),
            )

        return detect_changes(
            root_directory,
            self._scanner,
            self._metadata_extractor,
            self._indexer,
            cache,
        )

    def _off(
        self,
        changes: ChangeSet,
        started: float,
    ) -> FreshnessResult:
        return self._result(
            FreshnessState.OFF,
            changes,
            started,
            pending=changes.total,
            note=OFF_NOTE.format(n=changes.total),
        )

    def _failure(
        self,
        exc: Exception,
        changes: ChangeSet | None,
        started: float,
    ) -> FreshnessResult:
        total = changes.total if changes is not None else 0

        return self._result(
            FreshnessState.FAILED,
            changes,
            started,
            pending=total,
            note=FAILURE_NOTE.format(error=exc, n=total),
        )

    def _result(
        self,
        state: FreshnessState,
        changes: ChangeSet | None,
        started: float,
        updated: int = 0,
        pending: int = 0,
        note: str | None = None,
    ) -> FreshnessResult:
        return FreshnessResult(
            state=state,
            changed_files=len(changes.changed) if changes else 0,
            added_files=len(changes.added) if changes else 0,
            removed_files=len(changes.removed) if changes else 0,
            updated_files=updated,
            pending_files=pending,
            seconds=max(self._clock() - started, 0.0),
            note=note,
        )
