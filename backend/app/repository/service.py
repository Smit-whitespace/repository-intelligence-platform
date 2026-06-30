"""Repository service."""

from pathlib import Path

from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import (
    RepositoryEntry,
    RepositoryIndex,
    RepositorySummary,
)
from app.repository.scanner import RepositoryScanner


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

    def build_index(
        self,
        root_directory: Path,
    ) -> RepositoryIndex:
        """Build repository index."""

        entries = self._scanner.scan(
            root_directory,
        )

        enriched_entries: list[RepositoryEntry] = [
            self._metadata_extractor.enrich(
                entry,
            )
            for entry in entries
        ]

        files = sum(
            not entry.is_directory
            for entry in enriched_entries
        )

        directories = sum(
            entry.is_directory
            for entry in enriched_entries
        )

        total_size = sum(
            entry.size_bytes or 0
            for entry in enriched_entries
            if not entry.is_directory
        )

        return RepositoryIndex(
            summary=RepositorySummary(
                files=files,
                directories=directories,
                total_size_bytes=total_size,
            ),
            entries=enriched_entries,
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