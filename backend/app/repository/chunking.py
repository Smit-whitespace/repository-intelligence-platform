"""Repository document chunking."""

from app.repository.chunk_ids import generate_chunk_id
from app.repository.chunking_algorithms import (
    ChunkAlgorithm,
    LineChunkAlgorithm,
)
from app.repository.models import (
    ChunkBoundary,
    RepositoryChunk,
    RepositoryChunkMetadata,
    RepositoryDocument,
)
from app.repository.python_ast_algorithm import (
    PythonAstChunkAlgorithm,
)


class RepositoryChunker:
    """Repository chunk router."""

    def __init__(
        self,
    ) -> None:
        """Initialize chunk router."""

        self._default_algorithm: ChunkAlgorithm = (
            LineChunkAlgorithm()
        )

        self._language_algorithms: dict[
            str,
            ChunkAlgorithm,
        ] = {
            "Python": PythonAstChunkAlgorithm(),
        }

    def chunk(
        self,
        document: RepositoryDocument,
    ) -> list[RepositoryChunk]:
        """Chunk a repository document."""

        language = (
            document.entry.language
            or ""
        )

        algorithm = self._language_algorithms.get(
            language,
            self._default_algorithm,
        )

        try:
            boundaries = algorithm.generate_boundaries(
                document,
            )

        except SyntaxError:
            boundaries = self._default_algorithm.generate_boundaries(
                document,
            )

        return self._build_chunks(
            document=document,
            boundaries=boundaries,
        )

    def _build_chunks(
        self,
        document: RepositoryDocument,
        boundaries: list[ChunkBoundary],
    ) -> list[RepositoryChunk]:
        """Build repository chunks."""

        entry = document.entry

        if entry.sha256 is None:
            raise ValueError(
                "Repository entry must contain SHA-256."
            )

        document_lines = document.content.splitlines()

        chunks: list[
            RepositoryChunk
        ] = []

        for boundary in boundaries:
            metadata = RepositoryChunkMetadata(
                relative_path=entry.relative_path,
                language=entry.language,
                mime_type=entry.mime_type,
                sha256=entry.sha256,
            )

            chunks.append(
                RepositoryChunk(
                    chunk_id=generate_chunk_id(
                        entry=entry,
                        start_line=boundary.start_line,
                        end_line=boundary.end_line,
                    ),
                    entry=entry,
                    metadata=metadata,
                    boundary=boundary,
                    content="\n".join(
                        document_lines[
                            boundary.start_line - 1:
                            boundary.end_line
                        ]
                    ),
                )
            )

        return chunks

    def register_algorithm(
        self,
        language: str,
        algorithm: ChunkAlgorithm,
    ) -> None:
        """Register a language algorithm."""

        self._language_algorithms[
            language
        ] = algorithm