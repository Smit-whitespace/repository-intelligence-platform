"""Python AST chunk algorithm."""

from __future__ import annotations

import ast

from app.repository.chunking_algorithms import ChunkAlgorithm
from app.repository.models import (
    ChunkBoundary,
    ChunkType,
    RepositoryDocument,
)
from app.repository.python_parser import PythonParser


class PythonAstChunkAlgorithm(ChunkAlgorithm):
    """Generate chunk boundaries from Python AST."""

    def __init__(
        self,
    ) -> None:
        """Initialize the algorithm."""

        self._parser = PythonParser()

    def generate_boundaries(
        self,
        document: RepositoryDocument,
    ) -> list[ChunkBoundary]:
        """Generate semantic chunk boundaries."""

        module = self._parser.parse(
            document,
        )

        boundaries: list[ChunkBoundary] = []

        if not module.body:
            boundaries.append(
                ChunkBoundary(
                    start_line=1,
                    end_line=document.line_count,
                    chunk_type=ChunkType.MODULE,
                )
            )

            return boundaries

        for node in module.body:
            boundary = self._create_boundary(
                node=node,
                document=document,
            )

            if boundary is not None:
                boundaries.append(
                    boundary,
                )

        if not boundaries:
            boundaries.append(
                ChunkBoundary(
                    start_line=1,
                    end_line=document.line_count,
                    chunk_type=ChunkType.MODULE,
                )
            )

        return boundaries

    def _create_boundary(
        self,
        node: ast.AST,
        document: RepositoryDocument,
    ) -> ChunkBoundary | None:
        """Create a chunk boundary for a top-level node."""

        start_line = getattr(
            node,
            "lineno",
            None,
        )

        if start_line is None:
            return None

        end_line = getattr(
            node,
            "end_lineno",
            start_line,
        )

        if isinstance(
            node,
            ast.ClassDef,
        ):
            chunk_type = ChunkType.CLASS

        elif isinstance(
            node,
            ast.AsyncFunctionDef,
        ):
            chunk_type = ChunkType.ASYNC_FUNCTION

        elif isinstance(
            node,
            ast.FunctionDef,
        ):
            chunk_type = ChunkType.FUNCTION

        else:
            chunk_type = ChunkType.MODULE

        return ChunkBoundary(
            start_line=start_line,
            end_line=min(
                end_line,
                document.line_count,
            ),
            chunk_type=chunk_type,
        )