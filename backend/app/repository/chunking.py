"""Repository document chunking."""

from app.repository.models import (
    RepositoryChunk,
    RepositoryDocument,
)

_CHUNK_SIZE = 100


class RepositoryChunker:
    """Split repository documents into chunks."""

    def chunk(
        self,
        document: RepositoryDocument,
    ) -> list[RepositoryChunk]:
        """Split a document into line-based chunks."""

        lines = document.content.splitlines()

        chunks: list[RepositoryChunk] = []

        for start in range(
            0,
            len(lines),
            _CHUNK_SIZE,
        ):
            end = min(
                start + _CHUNK_SIZE,
                len(lines),
            )

            chunks.append(
                RepositoryChunk(
                    entry=document.entry,
                    content="\n".join(
                        lines[start:end],
                    ),
                    start_line=start + 1,
                    end_line=end,
                )
            )

        return chunks