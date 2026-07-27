"""Repository indexing service."""

from pathlib import Path

from app.indexing.indexer import RepositoryIndexer
from app.indexing.models import IndexingResult
from app.repository.chunking import RepositoryChunker
from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner


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

        entries = self._scanner.scan(
            root_directory,
        )

        scanned_files = 0

        indexed_files = 0

        indexed_chunks = 0

        skipped_files = 0

        failed_files = 0

        for entry in entries:
            if entry.is_directory:
                continue

            scanned_files += 1

            self._metadata_extractor.enrich(
                entry,
            )

            if not entry.is_text_file:
                skipped_files += 1

                continue

            try:
                document = self._document_loader.load(
                    entry,
                )

                chunks = self._chunker.chunk(
                    document,
                )

                result = self._indexer.index(
                    chunks,
                )

                indexed_files += 1

                indexed_chunks += result.indexed_chunks

            except Exception:
                #
                # Logging will be added once the
                # centralized logging subsystem
                # is implemented.
                #
                failed_files += 1

                continue

        return IndexingResult(
            scanned_files=scanned_files,
            indexed_files=indexed_files,
            indexed_chunks=indexed_chunks,
            skipped_files=skipped_files,
            failed_files=failed_files,
        )
