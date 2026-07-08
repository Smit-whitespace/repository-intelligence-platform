"""Repository chunking algorithms."""

from abc import ABC
from abc import abstractmethod
from app.repository.models import (
    ChunkBoundary,
    ChunkType,
    RepositoryDocument,
)

_LINE_CHUNK_SIZE = 100


class ChunkAlgorithm(ABC):
    """Repository chunk boundary algorithm."""

    @abstractmethod
    def generate_boundaries(
        self,
        document: RepositoryDocument,
    ) -> list[ChunkBoundary]:
        """Generate chunk boundaries."""


class LineChunkAlgorithm(ChunkAlgorithm):
    """Default line-based chunking algorithm."""

    def generate_boundaries(
        self,
        document: RepositoryDocument,
    ) -> list[ChunkBoundary]:
        """Generate line chunk boundaries."""

        document_lines = document.content.splitlines()

        boundaries: list[ 
            ChunkBoundary
        ] = []

        for start in range(
            0,
            len(document_lines),
            _LINE_CHUNK_SIZE,
        ):
            end = min(
                start + _LINE_CHUNK_SIZE,
                len(document_lines),
            )

            boundaries.append(
                ChunkBoundary(
                    start_line=start + 1,
                    end_line=end,
                    chunk_type=ChunkType.GENERIC,
                )
            )

        return boundaries