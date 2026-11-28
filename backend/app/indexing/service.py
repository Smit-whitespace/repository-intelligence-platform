"""Repository indexing service."""

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from app.indexing.exceptions import EmbeddingModelChangedError
from app.indexing.indexer import RepositoryIndexer
from app.indexing.lock import project_index_lock
from app.indexing.models import (
    FileFailureInfo,
    FileUpdateResult,
    IndexingDiagnostics,
    IndexingResult,
    IndexStatus,
)
from app.repository.chunking import RepositoryChunker
from app.repository.ignore import is_indexable_file_name
from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import RepositoryEntry
from app.repository.scanner import RepositoryScanner

logger = logging.getLogger(__name__)


@dataclass
class _FileOutcome:
    """What indexing one file produced."""

    is_text_file: bool = False
    indexed: bool = False
    chunk_ids: list[str] = field(default_factory=list)
    embedded_chunks: int = 0
    failure: FileFailureInfo | None = None
    content_failure: bool = False
    """The failure comes from the file's own content (it cannot be decoded
    or chunked), so retrying is useless until the file changes."""
    model_changed: bool = False
    """The configured embedding model was no longer ``expected_model``;
    nothing was written for this file."""


_CONTENT_STAGES = frozenset({"load", "chunking"})
"""Stages whose non-OS errors come from the file's content."""


class IndexingService:
    """Indexes an entire repository."""

    def __init__(
        self,
        scanner: RepositoryScanner,
        metadata_extractor: RepositoryMetadataExtractor,
        document_loader: RepositoryDocumentLoader,
        chunker: RepositoryChunker,
        indexer: RepositoryIndexer,
    ) -> None:
        """Initialize the indexing service."""

        self._scanner = scanner
        self._metadata_extractor = metadata_extractor
        self._document_loader = document_loader
        self._chunker = chunker
        self._indexer = indexer

    def index_repository(
        self,
        root_directory: Path,
    ) -> IndexingResult:
        """Index an entire repository.

        Holds the project's inter-process index lock for the whole run,
        so the RIP app and an MCP server never write the same index at
        once; a concurrent attempt raises ``IndexingBusyError``.
        """

        root_directory = root_directory.resolve()

        with project_index_lock(
            root_directory,
        ):
            return self._index_repository(
                root_directory,
            )

    def update_files(
        self,
        root_directory: Path,
        to_index: Sequence[str],
        to_remove: Sequence[str],
        deadline: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> FileUpdateResult:
        """Bring a given set of files in sync with the index.

        Paths are relative, in the stored form. Files in ``to_remove`` are
        dropped from the index first, then ``to_index`` is processed in
        order; no new file is started once ``clock()`` reaches
        ``deadline``, and the rest is reported as ``remaining``. A file
        that is gone or no longer indexable is removed instead. A failing
        file keeps its existing chunks; it is ``unindexable`` when its own
        content is the cause, ``failed`` otherwise.

        The configured embedding model is read once the lock is held. If
        it changes, or no longer matches the index, no further file is
        written: the rest is reported as ``remaining`` with
        ``model_changed``, so vectors are never stamped with a model that
        did not make them.

        Holds the project's inter-process index lock for the whole call;
        a concurrent attempt raises ``IndexingBusyError``.
        """

        root_directory = root_directory.resolve()

        root_directory_str = str(
            root_directory,
        )

        with project_index_lock(
            root_directory,
        ):
            self._indexer.remove_paths(
                root_directory_str,
                to_remove,
            )

            index_status = self._indexer.status(
                root_directory_str,
            )

            expected_model = index_status.configured_embedding_model

            model_changed = index_status.indexed and not index_status.compatible

            existing_chunk_ids = self._indexer.existing_chunk_ids(
                root_directory_str,
            )

            done: list[str] = []

            remaining: list[str] = []

            failed: list[str] = []

            unindexable: list[str] = []

            for relative_path in to_index:
                if not (remaining or model_changed):
                    model_changed = (
                        self._indexer.configured_embedding_model
                        != expected_model
                    )

                if (
                    remaining
                    or model_changed
                    or (deadline is not None and clock() >= deadline)
                ):
                    remaining.append(
                        relative_path,
                    )

                    continue

                absolute_path = root_directory / relative_path

                entry = RepositoryEntry(
                    name=absolute_path.name,
                    absolute_path=absolute_path,
                    relative_path=Path(
                        relative_path,
                    ),
                    is_directory=False,
                )

                outcome = (
                    self._index_file(
                        entry,
                        root_directory_str,
                        existing_chunk_ids,
                        expected_model=expected_model,
                    )
                    if absolute_path.is_file()
                    and is_indexable_file_name(
                        entry.name,
                    )
                    else None
                )

                if outcome is not None and outcome.model_changed:
                    model_changed = True

                    remaining.append(
                        relative_path,
                    )

                    continue

                if outcome is not None and outcome.failure is not None:
                    (unindexable if outcome.content_failure else failed).append(
                        relative_path,
                    )

                    continue

                # Gone, or no longer an indexable text file: not in the index.
                if outcome is None or not outcome.indexed:
                    self._indexer.remove_paths(
                        root_directory_str,
                        [relative_path],
                    )

                else:
                    self._indexer.remove_chunks_of_path_except(
                        root_directory_str,
                        relative_path,
                        outcome.chunk_ids,
                    )

                done.append(
                    relative_path,
                )

        if model_changed:
            logger.warning(
                "Stopped updating the index for %s: the embedding model "
                "changed from %s to %s; %d files were not updated. "
                "Reindex to use the new model.",
                root_directory,
                expected_model,
                self._indexer.configured_embedding_model,
                len(remaining),
            )

        return FileUpdateResult(
            done=done,
            remaining=remaining,
            failed=failed,
            unindexable=unindexable,
            model_changed=model_changed,
        )

    def status(
        self,
        root_directory: Path,
    ) -> IndexStatus:
        """Report whether a project is indexed, and with which model."""

        return self._indexer.status(
            str(
                root_directory.resolve(),
            ),
        )

    def _index_repository(
        self,
        root_directory: Path,
    ) -> IndexingResult:
        """Index a resolved repository root (the lock is held)."""

        root_directory_str = str(
            root_directory,
        )

        start_time = time.monotonic()

        self._indexer.prepare(
            root_directory_str,
        )

        existing_chunk_ids = self._indexer.existing_chunk_ids(
            root_directory_str,
        )

        # A file that fails this run (locked, temporarily unreadable,
        # provider hiccup) keeps the chunks it already had, instead of
        # having its valid vectors removed as "stale".
        existing_by_path = self._indexer.existing_chunk_ids_by_path(
            root_directory_str,
        )

        unchanged_files = 0

        entries = self._scanner.scan(
            root_directory,
        )

        total_files_discovered = 0

        text_files_detected = 0

        scanned_files = 0

        indexed_files = 0

        indexed_chunks = 0

        skipped_files = 0

        failed_files = 0

        indexed_chunk_ids: list[str] = []

        failures: list[FileFailureInfo] = []

        for entry in entries:
            if entry.is_directory:
                continue

            total_files_discovered += 1

            scanned_files += 1

            if not is_indexable_file_name(
                entry.name,
            ):
                skipped_files += 1

                continue

            outcome = self._index_file(
                entry,
                root_directory_str,
                existing_chunk_ids,
            )

            if outcome.is_text_file:
                text_files_detected += 1

            if outcome.failure is not None:
                failures.append(
                    outcome.failure,
                )

                failed_files += 1

                indexed_chunk_ids.extend(
                    existing_by_path.get(
                        str(
                            entry.relative_path,
                        ),
                        (),
                    ),
                )

            elif outcome.indexed:
                indexed_files += 1

                indexed_chunks += outcome.embedded_chunks

                if outcome.embedded_chunks == 0:
                    unchanged_files += 1

                # Every current chunk is kept, embedded now or earlier.
                indexed_chunk_ids.extend(
                    outcome.chunk_ids,
                )

            else:
                skipped_files += 1

        # When every file failed (typically: the embedding provider is
        # down), the keep-list is empty only because nothing could be
        # embedded, not because the files are gone. Removing "stale"
        # chunks then would wipe the whole existing index.
        if indexed_files > 0 or failed_files == 0:
            self._indexer.remove_stale_chunks(
                root_directory=root_directory_str,
                keep_chunk_ids=indexed_chunk_ids,
            )

        else:
            logger.warning(
                "Kept the existing index for %s: all %d files failed to index",
                root_directory,
                failed_files,
            )

        elapsed_ms = int(
            (time.monotonic() - start_time)
            * 1000,
        )

        diagnostics = IndexingDiagnostics(
            total_files_discovered=total_files_discovered,
            text_files_detected=text_files_detected,
            total_chunks_created=indexed_chunks,
            indexing_duration_ms=elapsed_ms,
            failed_files_details=failures,
        )

        logger.info(
            "Indexed %s: %d files (%d unchanged), %d skipped, %d failed, "
            "%d chunks embedded in %d ms",
            root_directory,
            indexed_files,
            unchanged_files,
            skipped_files,
            failed_files,
            indexed_chunks,
            elapsed_ms,
        )

        return IndexingResult(
            scanned_files=scanned_files,
            indexed_files=indexed_files,
            indexed_chunks=indexed_chunks,
            skipped_files=skipped_files,
            failed_files=failed_files,
            unchanged_files=unchanged_files,
            diagnostics=diagnostics,
        )

    def _index_file(
        self,
        entry: RepositoryEntry,
        root_directory_str: str,
        existing_chunk_ids: set[str],
        expected_model: str | None = None,
    ) -> _FileOutcome:
        """Load, chunk and embed one file; never raises.

        Shared by a full run and ``update_files``. Chunk ids include the
        file's content hash, so a chunk whose id is already indexed is
        unchanged and keeps its vector: only new or edited content is
        embedded. A failure is returned, not raised, so the caller can
        keep the file's existing chunks. With ``expected_model``, nothing
        is written once another model is configured (``model_changed``).
        """

        relative_path = str(
            entry.relative_path,
        )

        outcome = _FileOutcome()

        stage = "metadata"

        try:
            self._metadata_extractor.enrich(
                entry,
            )

            outcome.is_text_file = bool(
                entry.is_text_file,
            )

            if not outcome.is_text_file:
                return outcome

            stage = "load"

            document = self._document_loader.load(
                entry,
            )

            stage = "chunking"

            chunks = self._chunker.chunk(
                document,
            )

            for chunk in chunks:
                chunk.metadata = chunk.metadata.model_copy(
                    update={
                        "root_directory": root_directory_str,
                    },
                )

            stage = "indexing"

            new_chunks = [
                chunk
                for chunk in chunks
                if chunk.chunk_id not in existing_chunk_ids
            ]

            if new_chunks:
                outcome.embedded_chunks = self._indexer.index(
                    new_chunks,
                    expected_model=expected_model,
                ).indexed_chunks

        except EmbeddingModelChangedError:
            outcome.model_changed = True

            return outcome

        except Exception as exc:
            outcome.failure = FileFailureInfo(
                relative_path=relative_path,
                stage=stage,
                exception_type=type(
                    exc,
                ).__name__,
                message=str(
                    exc,
                ),
            )

            # A decode or chunking error repeats until the file changes;
            # an OS error (locked, vanished) or a provider error may not.
            outcome.content_failure = stage in _CONTENT_STAGES and not isinstance(
                exc,
                OSError,
            )

            logger.warning(
                "Failed %s for %s: %s: %s",
                stage,
                relative_path,
                type(
                    exc,
                ).__name__,
                exc,
            )

            return outcome

        outcome.indexed = True

        outcome.chunk_ids = [
            chunk.chunk_id
            for chunk in chunks
        ]

        return outcome
