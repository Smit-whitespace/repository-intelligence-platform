"""Tests for repository service."""

from pathlib import Path

from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner
from app.repository.service import RepositoryService


def test_build_index(
    tmp_path: Path,
) -> None:
    """Repository index should be built."""

    (tmp_path / "README.md").write_text(
        "hello",
        encoding="utf-8",
    )

    service = RepositoryService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
    )

    index = service.build_index(
        tmp_path,
    )

    assert index.summary.files == 1
    assert index.summary.directories == 0
    assert index.summary.total_size_bytes == 5
    assert len(index.entries) == 1