"""Tests for chunk algorithms."""

from pathlib import Path

from app.repository.chunking_algorithms import (
    LineChunkAlgorithm,
)
from app.repository.documents import (
    RepositoryDocumentLoader,
)
from app.repository.metadata import (
    RepositoryMetadataExtractor,
)
from app.repository.models import (
    RepositoryEntry,
)


def test_line_algorithm(
    tmp_path: Path,
) -> None:
    """Line algorithm should chunk documents."""

    file_path = tmp_path / "main.py"

    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="main.py",
        absolute_path=file_path,
        relative_path=Path("main.py"),
        is_directory=False,
    )

    extractor = RepositoryMetadataExtractor()

    extractor.enrich_fast(
        entry,
    )

    extractor.enrich_slow(
        entry,
    )

    document = RepositoryDocumentLoader().load(
        entry,
    )

    boundaries = (
        LineChunkAlgorithm()
        .generate_boundaries(
            document,
        )
    )

    assert len(boundaries) == 1

    assert boundaries[0].start_line == 1

    assert boundaries[0].end_line == 1

