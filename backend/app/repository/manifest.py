"""Repository manifest generation."""

from app.repository.models import (
    RepositoryEntry,
    RepositoryManifest,
)


class RepositoryManifestBuilder:
    """Build repository manifests."""

    def build(
        self,
        entries: list[RepositoryEntry],
    ) -> RepositoryManifest:
        """Build a repository manifest."""

        return RepositoryManifest(
            files=[
                entry
                for entry in entries
                if not entry.is_directory
            ],
            directories=[
                entry
                for entry in entries
                if entry.is_directory
            ],
        )