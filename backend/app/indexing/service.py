"""Repository indexing service."""

import logging
import time
from pathlib import Path

from app.indexing.indexer import RepositoryIndexer
from app.indexing.models import (
    FileFailureInfo,
    IndexingDiagnostics,
    IndexingResult,
)
from app.repository.chunking import RepositoryChunker
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
        """Index an entire repository."""

        root_directory = root_directory.resolve()

        root_directory_str = str(
            root_directory,
        )

        start_time = time.monotonic()

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

            try:
                result = self._indexer.index(
                    chunks,
                )

                indexed_files += 1

                indexed_chunks += result.indexed_chunks

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

        self._indexer.remove_stale_chunks(
            root_directory=root_directory_str,
            keep_chunk_ids=indexed_chunk_ids,
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
            "Indexed %s: %d files, %d skipped, %d failed, "
            "%d chunks in %d ms",
            root_directory,
            indexed_files,
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
            diagnostics=diagnostics,
        )
