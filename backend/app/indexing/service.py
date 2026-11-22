"""Repository indexing service."""

import logging
import time
from pathlib import Path

from app.indexing.indexer import RepositoryIndexer
from app.indexing.lock import project_index_lock
from app.indexing.models import (
    FileFailureInfo,
    IndexingDiagnostics,
    IndexingResult,
    IndexStatus,
)
from app.repository.chunking import RepositoryChunker
from app.repository.ignore import is_indexable_file_name
from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner

logger = logging.getLogger(__name__)


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

            relative_path = str(
                entry.relative_path,
            )

            try:
                self._metadata_extractor.enrich(
                    entry,
                )

                if entry.is_text_file:
                    text_files_detected += 1

                if not entry.is_text_file:
                    skipped_files += 1

                    continue

            except Exception as exc:
                failures.append(
                    FileFailureInfo(
                        relative_path=relative_path,
                        stage="metadata",
                        exception_type=type(
                            exc,
                        ).__name__,
                        message=str(
                            exc,
                        ),
                    ),
                )

                logger.warning(
                    "Failed metadata for %s: %s: %s",
                    relative_path,
                    type(
                        exc,
                    ).__name__,
                    exc,
                )

                failed_files += 1

                continue

            try:
                document = self._document_loader.load(
                    entry,
                )

            except Exception as exc:
                failures.append(
                    FileFailureInfo(
                        relative_path=relative_path,
                        stage="load",
                        exception_type=type(
                            exc,
                        ).__name__,
                        message=str(
                            exc,
                        ),
                    ),
                )

                logger.warning(
                    "Failed to load %s: %s: %s",
                    relative_path,
                    type(
                        exc,
                    ).__name__,
                    exc,
                )

                failed_files += 1

                continue

            try:
                chunks = self._chunker.chunk(
                    document,
                )

            except Exception as exc:
                failures.append(
                    FileFailureInfo(
                        relative_path=relative_path,
                        stage="chunking",
                        exception_type=type(
                            exc,
                        ).__name__,
                        message=str(
                            exc,
                        ),
                    ),
                )

                logger.warning(
                    "Failed to chunk %s: %s: %s",
                    relative_path,
                    type(
                        exc,
                    ).__name__,
                    exc,
                )

                failed_files += 1

                continue

            for chunk in chunks:
                chunk.metadata = chunk.metadata.model_copy(
                    update={
                        "root_directory": root_directory_str,
                    },
                )

            # Chunk ids include the file's content hash, so a chunk whose
            # id is already indexed is unchanged and keeps its vector.
            # Only new or edited content is embedded.
            new_chunks = [
                chunk
                for chunk in chunks
                if chunk.chunk_id not in existing_chunk_ids
            ]

            try:
                if new_chunks:
                    result = self._indexer.index(
                        new_chunks,
                    )

                    indexed_chunks += result.indexed_chunks

                else:
                    unchanged_files += 1

                indexed_files += 1

                # Every current chunk is kept, embedded now or earlier.
                indexed_chunk_ids.extend(
                    chunk.chunk_id
                    for chunk in chunks
                )

            except Exception as exc:
                failures.append(
                    FileFailureInfo(
                        relative_path=relative_path,
                        stage="indexing",
                        exception_type=type(
                            exc,
                        ).__name__,
                        message=str(
                            exc,
                        ),
                    ),
                )

                logger.warning(
                    "Failed to index %s: %s: %s",
                    relative_path,
                    type(
                        exc,
                    ).__name__,
                    exc,
                )

                failed_files += 1

                continue

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
