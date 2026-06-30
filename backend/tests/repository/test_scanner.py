"""Tests for the repository scanner."""

from pathlib import Path

from app.repository.scanner import RepositoryScanner

import pytest
from app.repository.exceptions import RepositoryScanError

def test_scan_returns_file(
    tmp_path: Path,
) -> None:
    """Scanner should discover files."""

    (tmp_path / "README.md").write_text(
        "hello",
        encoding="utf-8",
    )

    scanner = RepositoryScanner()

    entries = scanner.scan(tmp_path)

    assert len(entries) == 1
    assert entries[0].name == "README.md"
    assert not entries[0].is_directory


def test_scan_returns_directory(
    tmp_path: Path,
) -> None:
    """Scanner should discover directories."""

    (tmp_path / "src").mkdir()

    scanner = RepositoryScanner()

    entries = scanner.scan(tmp_path)

    assert len(entries) == 1
    assert entries[0].name == "src"
    assert entries[0].is_directory


def test_scan_ignores_internal_directory(
    tmp_path: Path,
) -> None:
    """Scanner should ignore .local_openclaw."""

    ignored = tmp_path / ".local_openclaw"

    ignored.mkdir()

    (ignored / "project.json").write_text(
        "{}",
        encoding="utf-8",
    )

    scanner = RepositoryScanner()

    entries = scanner.scan(tmp_path)

    assert entries == []


def test_scan_returns_sorted_results(
    tmp_path: Path,
) -> None:
    """Scanner should return sorted entries."""

    (tmp_path / "z.txt").write_text(
        "",
        encoding="utf-8",
    )

    (tmp_path / "a.txt").write_text(
        "",
        encoding="utf-8",
    )

    scanner = RepositoryScanner()

    entries = scanner.scan(tmp_path)

    assert [
        entry.name
        for entry in entries
    ] == [
        "a.txt",
        "z.txt",
    ]

def test_scan_nonexistent_directory(
    tmp_path: Path,
) -> None:
    """Scanner should reject nonexistent repositories."""

    scanner = RepositoryScanner()

    with pytest.raises(
        RepositoryScanError,
    ):
        scanner.scan(
            tmp_path / "missing",
        )


def test_scan_file_instead_of_directory(
    tmp_path: Path,
) -> None:
    """Scanner should reject files."""

    file_path = tmp_path / "file.txt"

    file_path.write_text(
        "hello",
        encoding="utf-8",
    )

    scanner = RepositoryScanner()

    with pytest.raises(
        RepositoryScanError,
    ):
        scanner.scan(
            file_path,
        )