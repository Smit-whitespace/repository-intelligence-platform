"""Repository service."""

from pathlib import Path

from app.repository.manifest import RepositoryManifestBuilder
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import (
    RepositoryEntry,
    RepositoryIndex,
    RepositoryManifest,
    RepositorySummary,
    RepositoryDocument,
)
from app.repository.scanner import RepositoryScanner
from app.repository.documents import RepositoryDocumentLoader
from app.repository.chunking import RepositoryChunker
from app.repository.models import RepositoryChunk


class RepositoryService:
    """Repository service."""

    def __init__(
        self,
        scanner: RepositoryScanner,
        metadata_extractor: RepositoryMetadataExtractor,
    ) -> None:
        """Initialize repository service."""

        self._scanner = scanner
        self._metadata_extractor = metadata_extractor
        self._manifest_builder = RepositoryManifestBuilder()
        self._document_loader = RepositoryDocumentLoader()
        self._chunker = RepositoryChunker()

    def build_index(
        self,
        root_directory: Path,
    ) -> RepositoryIndex:
        """Build repository index."""

        entries = [
            self._metadata_extractor.enrich(
                entry,
            )
            for entry in self._scanner.scan(
                root_directory,
            )
        ]

        return RepositoryIndex(
            summary=RepositorySummary(
                files=sum(
                    not entry.is_directory
                    for entry in entries
                ),
                directories=sum(
                    entry.is_directory
                    for entry in entries
                ),
                total_size_bytes=sum(
                    entry.size_bytes or 0
                    for entry in entries
                    if not entry.is_directory
                ),
            ),
            entries=entries,
        )

    def build_manifest(
        self,
        root_directory: Path,
    ) -> RepositoryManifest:
        """Build repository manifest."""

        return self._manifest_builder.build(
            self.build_index(
                root_directory,
            ).entries,
        )

    def scan(
        self,
        root_directory: Path,
    ) -> list[RepositoryEntry]:
        """Return repository entries."""

        return self.build_index(
            root_directory,
        ).entries

    def summary(
        self,
        root_directory: Path,
    ) -> RepositorySummary:
        """Return repository summary."""

        return self.build_index(
            root_directory,
        ).summary
    
    def load_documents(
        self,
        root_directory: Path,
    ) -> list[RepositoryDocument]:
        """Load repository documents."""

        documents = []

        for entry in self.scan(
            root_directory,
        ):
            if (
                entry.is_directory
                or not entry.is_text_file
            ):
                continue

            documents.append(
                self._document_loader.load(
                    entry,
                )
            )

        return documents
    
    def build_chunks(
        self,
        root_directory: Path,
    ) -> list[RepositoryChunk]:
        """Build repository chunks."""

        chunks: list[RepositoryChunk] = []

        for document in self.load_documents(
            root_directory,
        ):
            chunks.extend(
                self._chunker.chunk(
                    document,
                )
            )

        return chunks