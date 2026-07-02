"""Repository metadata extraction."""

from datetime import UTC
from datetime import datetime

from app.repository.filetypes import is_text_file
from app.repository.hashing import calculate_sha256
from app.repository.languages import detect_language
from app.repository.mime import detect_mime_type
from app.repository.models import RepositoryEntry


class RepositoryMetadataExtractor:
    """Populate repository metadata."""

    def enrich_fast(
        self,
        entry: RepositoryEntry,
    ) -> RepositoryEntry:
        """Populate inexpensive metadata."""

        stat = entry.absolute_path.stat()

        entry.size_bytes = stat.st_size

        entry.modified_at = datetime.fromtimestamp(
            stat.st_mtime,
            tz=UTC,
        )

        if entry.is_directory:
            return entry

        entry.language = detect_language(
            entry.absolute_path,
        )

        entry.is_text_file = is_text_file(
            entry.absolute_path,
        )

        entry.mime_type = detect_mime_type(
            entry.absolute_path,
        )

        return entry

    def enrich_slow(
        self,
        entry: RepositoryEntry,
    ) -> RepositoryEntry:
        """Populate expensive metadata."""

        if (
            entry.is_directory
            or not entry.is_text_file
        ):
            return entry

        entry.sha256 = calculate_sha256(
            entry.absolute_path,
        )

        return entry

    def enrich(
        self,
        entry: RepositoryEntry,
    ) -> RepositoryEntry:
        """Populate all metadata."""

        self.enrich_fast(
            entry,
        )

        self.enrich_slow(
            entry,
        )

        return entry