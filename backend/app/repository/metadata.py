"""Repository metadata extraction."""

from datetime import UTC
from datetime import datetime

from app.repository.hashing import calculate_sha256
from app.repository.languages import detect_language
from app.repository.models import RepositoryEntry
from app.repository.filetypes import is_text_file
from app.repository.mime import detect_mime_type


class RepositoryMetadataExtractor:
    """Populate repository metadata."""

    def enrich(
        self,
        entry: RepositoryEntry,
    ) -> RepositoryEntry:
        """Populate metadata."""

        stat = entry.absolute_path.stat()

        entry.size_bytes = stat.st_size

        entry.modified_at = datetime.fromtimestamp(
            stat.st_mtime,
            tz=UTC,
        )

        if not entry.is_directory:
            entry.language = detect_language(
                entry.absolute_path,
            )

            entry.is_text_file = is_text_file(
                entry.absolute_path,
            )  

            entry.mime_type = detect_mime_type(
                entry.absolute_path,
            ) 

            entry.sha256 = calculate_sha256(
                entry.absolute_path,
            )

        return entry