"""Repository document loading."""

from app.repository.models import (
    RepositoryDocument,
    RepositoryEntry,
)


class RepositoryDocumentLoader:
    """Load repository documents."""

    def load(
        self,
        entry: RepositoryEntry,
    ) -> RepositoryDocument:
        """Load a text document."""

        content = entry.absolute_path.read_text(
            encoding="utf-8",
        )

        return RepositoryDocument(
            entry=entry,
            content=content,
            line_count=len(
                content.splitlines(),
            ),
        )