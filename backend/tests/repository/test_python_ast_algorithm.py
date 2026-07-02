"""Tests for the Python AST chunk algorithm."""

from pathlib import Path

from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import (
    ChunkType,
    RepositoryEntry,
)
from app.repository.python_ast_algorithm import (
    PythonAstChunkAlgorithm,
)


def _load_document(
    file_path: Path,
):
    """Load a repository document."""

    entry = RepositoryEntry(
        name=file_path.name,
        absolute_path=file_path,
        relative_path=Path(file_path.name),
        is_directory=False,
    )

    extractor = RepositoryMetadataExtractor()

    extractor.enrich_fast(
        entry,
    )

    extractor.enrich_slow(
        entry,
    )

    return RepositoryDocumentLoader().load(
        entry,
    )


def test_python_function_chunk(
    tmp_path: Path,
) -> None:
    """Functions should become function chunks."""

    file_path = tmp_path / "main.py"

    file_path.write_text(
        "def hello():\n"
        "    return 1\n",
        encoding="utf-8",
    )

    document = _load_document(
        file_path,
    )

    boundaries = (
        PythonAstChunkAlgorithm()
        .generate_boundaries(
            document,
        )
    )

    assert len(boundaries) == 1

    assert boundaries[0].chunk_type == ChunkType.FUNCTION


def test_python_class_chunk(
    tmp_path: Path,
) -> None:
    """Classes should become class chunks."""

    file_path = tmp_path / "main.py"

    file_path.write_text(
        "class User:\n"
        "    pass\n",
        encoding="utf-8",
    )

    document = _load_document(
        file_path,
    )

    boundaries = (
        PythonAstChunkAlgorithm()
        .generate_boundaries(
            document,
        )
    )

    assert boundaries[0].chunk_type == ChunkType.CLASS