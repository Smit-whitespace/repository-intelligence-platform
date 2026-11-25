"""Python AST chunk algorithm."""

from __future__ import annotations

import ast

from app.repository.chunking_algorithms import (
    LINE_CHUNK_SIZE,
    ChunkAlgorithm,
)
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

        boundaries = _merge_module_statements(
            boundaries,
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

        # A decorated definition starts at its first decorator: for a
        # route, the decorator holds the URL, which search must see.
        for decorator in getattr(
            node,
            "decorator_list",
            [],
        ):
            start_line = min(
                start_line,
                decorator.lineno,
            )

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


def _merge_module_statements(
    boundaries: list[ChunkBoundary],
) -> list[ChunkBoundary]:
    """Join consecutive top-level statements into one module chunk.

    Without this, every import and constant became its own one-line
    chunk, and those crowded real code out of search results. A merged
    chunk spans from its first statement to its last, so comments in
    between stay with them, and never grows past ``LINE_CHUNK_SIZE``
    lines (a single longer statement stays whole).
    """

    merged: list[ChunkBoundary] = []

    for boundary in boundaries:
        previous = merged[-1] if merged else None

        if (
            previous is not None
            and previous.chunk_type is ChunkType.MODULE
            and boundary.chunk_type is ChunkType.MODULE
            and boundary.end_line - previous.start_line < LINE_CHUNK_SIZE
        ):
            merged[-1] = ChunkBoundary(
                start_line=previous.start_line,
                end_line=boundary.end_line,
                chunk_type=ChunkType.MODULE,
            )

            continue

        merged.append(
            boundary,
        )

    return merged