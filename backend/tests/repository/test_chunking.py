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