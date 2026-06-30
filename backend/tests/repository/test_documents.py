"""Tests for repository documents."""

from pathlib import Path

from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import RepositoryEntry


def test_document_loader(
    tmp_path: Path,
) -> None:
    """Document loader should read text."""

    file_path = tmp_path / "hello.py"

    file_path.write_text(
        "print('hello')\nprint('world')",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="hello.py",
        absolute_path=file_path,
        relative_path=Path("hello.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich(
        entry,
    )

    document = RepositoryDocumentLoader().load(
        entry,
    )

    assert document.content.startswith(
        "print"
    )

    assert document.line_count == 2