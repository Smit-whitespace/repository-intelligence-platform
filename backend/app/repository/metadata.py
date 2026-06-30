"""Repository metadata extraction."""

from datetime import UTC
from datetime import datetime

from app.repository.models import RepositoryEntry


class RepositoryMetadataExtractor:
    """Populate repository metadata."""

    def enrich(
        self,
        entry: RepositoryEntry,
    ) -> RepositoryEntry:
        """Populate filesystem metadata."""

        stat = entry.absolute_path.stat()

        entry.size_bytes = stat.st_size

        entry.modified_at = datetime.fromtimestamp(
            stat.st_mtime,
            tz=UTC,
        )

        return entry