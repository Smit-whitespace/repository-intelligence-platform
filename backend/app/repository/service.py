"""Repository service."""

from pathlib import Path

from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import RepositoryEntry
from app.repository.scanner import RepositoryScanner


class RepositoryService:
    """Repository service."""

    def __init__(
        self,
        scanner: RepositoryScanner,
        metadata_extractor: RepositoryMetadataExtractor,
    ) -> None:
        """Initialize the repository service."""

        self._scanner = scanner
        self._metadata_extractor = metadata_extractor

    def scan(
        self,
        root_directory: Path,
    ) -> list[RepositoryEntry]:
        """Scan a repository and enrich entries with metadata."""

        entries = self._scanner.scan(
            root_directory,
        )

        return [
            self._metadata_extractor.enrich(
                entry,
            )
            for entry in entries
        ]