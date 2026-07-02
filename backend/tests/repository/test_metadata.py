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

    file_path = tmp_path / "hello.py"

    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="hello.py",
        absolute_path=file_path,
        relative_path=Path("hello.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich_fast(
        entry,
    )

    assert entry.size_bytes is not None
    assert entry.size_bytes > 0


def test_metadata_sets_modified_time(
    tmp_path: Path,
) -> None:
    """Metadata extractor should populate modified time."""

    file_path = tmp_path / "hello.py"

    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="hello.py",
        absolute_path=file_path,
        relative_path=Path("hello.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich_fast(
        entry,
    )

    assert entry.modified_at is not None


def test_metadata_detects_language(
    tmp_path: Path,
) -> None:
    """Metadata extractor should detect language."""

    file_path = tmp_path / "hello.py"

    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="hello.py",
        absolute_path=file_path,
        relative_path=Path("hello.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich_fast(
        entry,
    )

    assert entry.language == "Python"

def test_metadata_calculates_sha256(
    tmp_path: Path,
) -> None:
    """Metadata extractor should calculate SHA-256."""

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

    extractor = RepositoryMetadataExtractor()

    extractor.enrich_fast(
        entry,
    )

    extractor.enrich_slow(
        entry,
    )

    assert entry.sha256 is not None
    assert len(entry.sha256) == 64

def test_metadata_detects_text_file(
    tmp_path: Path,
) -> None:
    """Metadata extractor should detect text files."""

    file_path = tmp_path / "hello.py"

    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="hello.py",
        absolute_path=file_path,
        relative_path=Path("hello.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich_fast(
        entry,
    )

    assert entry.is_text_file is not None
    assert entry.is_text_file is True

def test_metadata_detects_mime_type(
    tmp_path: Path,
) -> None:
    """Metadata extractor should detect MIME type."""

    file_path = tmp_path / "hello.json"

    file_path.write_text(
        "{}",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="hello.json",
        absolute_path=file_path,
        relative_path=Path("hello.json"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich_fast(
        entry,
    )

    assert entry.mime_type is not None
    assert entry.mime_type == "application/json"