"""Tests for repository chunking."""

from pathlib import Path

from app.repository.chunking import RepositoryChunker
from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import RepositoryEntry


def test_chunk_single_document(
    tmp_path: Path,
) -> None:
    """Chunk a small document."""

    file_path = tmp_path / "example.py"

    file_path.write_text(
        "\n".join(
            f"line {number}"
            for number in range(
                1,
                11,
            )
        ),
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="example.py",
        absolute_path=file_path,
        relative_path=Path("example.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich(
        entry,
    )

    document = RepositoryDocumentLoader().load(
        entry,
    )

    chunks = RepositoryChunker().chunk(
        document,
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.start_line == 1
    assert chunk.end_line == 10
    assert "line 1" in chunk.content
    assert "line 10" in chunk.content
    assert chunk.metadata.relative_path == Path(
        "example.py",
    )


def test_chunk_id_is_generated(
    tmp_path: Path,
) -> None:
    """Chunk IDs should be generated."""

    file_path = tmp_path / "example.py"

    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="example.py",
        absolute_path=file_path,
        relative_path=Path("example.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich(
        entry,
    )

    document = RepositoryDocumentLoader().load(
        entry,
    )

    chunk = RepositoryChunker().chunk(
        document,
    )[0]

    assert len(chunk.chunk_id) == 64

    assert chunk.metadata.relative_path == Path(
    "example.py",
)

    assert chunk.metadata.language == "Python"

    assert chunk.metadata.sha256 is not None


def test_chunk_id_is_deterministic(
    tmp_path: Path,
) -> None:
    """Chunk IDs should be deterministic."""

    file_path = tmp_path / "example.py"

    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="example.py",
        absolute_path=file_path,
        relative_path=Path("example.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich(
        entry,
    )

    loader = RepositoryDocumentLoader()

    document = loader.load(
        entry,
    )

    chunker = RepositoryChunker()

    first = chunker.chunk(
        document,
    )[0]

    second = chunker.chunk(
        document,
    )[0]

    assert first.chunk_id == second.chunk_id

def test_invalid_python_falls_back_to_line_chunking(
    tmp_path: Path,
) -> None:
    """Invalid Python should fall back to line chunking."""

    file_path = tmp_path / "broken.py"

    file_path.write_text(
        "line 1\nline 2",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="broken.py",
        absolute_path=file_path,
        relative_path=Path("broken.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich(
        entry,
    )

    document = RepositoryDocumentLoader().load(
        entry,
    )

    chunks = RepositoryChunker().chunk(
        document,
    )

    assert len(chunks) == 1

    assert chunks[0].start_line == 1

    assert chunks[0].end_line == 2