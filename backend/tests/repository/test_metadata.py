"""Tests for repository metadata."""

from pathlib import Path

from app.repository.metadata import (
    RepositoryMetadataExtractor,
)
from app.repository.models import (
    RepositoryEntry,
)


def test_metadata_sets_file_size(
    tmp_path: Path,
) -> None:
    """Metadata extractor should populate size."""

    file_path = tmp_path / "hello.txt"

    file_path.write_text(
        "hello",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="hello.txt",
        absolute_path=file_path,
        relative_path=Path("hello.txt"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich(
        entry,
    )

    assert entry.size_bytes == 5


def test_metadata_sets_modified_time(
    tmp_path: Path,
) -> None:
    """Metadata extractor should populate modified time."""

    file_path = tmp_path / "hello.txt"

    file_path.write_text(
        "hello",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="hello.txt",
        absolute_path=file_path,
        relative_path=Path("hello.txt"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich(
        entry,
    )

    assert entry.modified_at is not None