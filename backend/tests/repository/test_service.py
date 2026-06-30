"""Tests for the repository service."""

from pathlib import Path

from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner
from app.repository.service import RepositoryService


def test_repository_service_returns_metadata(
    tmp_path: Path,
) -> None:
    """Repository service should return enriched entries."""

    (tmp_path / "README.md").write_text(
        "hello",
        encoding="utf-8",
    )

    service = RepositoryService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
    )

    entries = service.scan(
        tmp_path,
    )

    assert len(entries) == 1

    entry = entries[0]

    assert entry.name == "README.md"
    assert entry.size_bytes == 5
    assert entry.modified_at is not None