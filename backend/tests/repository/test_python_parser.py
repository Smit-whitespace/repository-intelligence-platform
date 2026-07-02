"""Tests for the Python parser."""

from pathlib import Path

from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import RepositoryEntry
from app.repository.python_parser import PythonParser


def test_parse_python_document(
    tmp_path: Path,
) -> None:
    """Parser should return a module."""

    file_path = tmp_path / "main.py"

    file_path.write_text(
        "def hello():\n    return 1\n",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="main.py",
        absolute_path=file_path,
        relative_path=Path("main.py"),
        is_directory=False,
    )

    extractor = RepositoryMetadataExtractor()

    extractor.enrich_fast(entry)
    extractor.enrich_slow(entry)

    document = RepositoryDocumentLoader().load(
        entry,
    )

    module = PythonParser().parse(
        document,
    )

    assert len(module.body) == 1