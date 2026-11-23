"""Tests for the repository scanner."""

from pathlib import Path

from app.repository.scanner import RepositoryScanner

import pytest
from app.repository.exceptions import RepositoryScanError

def test_scan_discovers_mjs(
    tmp_path: Path,
) -> None:
    """Scanner should discover .mjs files."""

    (
        tmp_path / "module.mjs"
    ).write_text(
        "export const x = 1;",
        encoding="utf-8",
    )

    scanner = RepositoryScanner()

    entries = scanner.scan(
        tmp_path,
    )

    names = [
        e.name
        for e in entries
        if not e.is_directory
    ]

    assert "module.mjs" in names


def test_scan_discovers_cjs(
    tmp_path: Path,
) -> None:
    """Scanner should discover .cjs files."""

    (
        tmp_path / "config.cjs"
    ).write_text(
        "module.exports = {};",
        encoding="utf-8",
    )

    scanner = RepositoryScanner()

    entries = scanner.scan(
        tmp_path,
    )

    names = [
        e.name
        for e in entries
        if not e.is_directory
    ]

    assert "config.cjs" in names


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


def test_scan_ignores_internal_directories(
    tmp_path: Path,
) -> None:
    """Scanner should ignore the canonical and legacy internal dirs."""

    canonical = tmp_path / ".local_openclaw"

    canonical.mkdir()

    (canonical / "project.json").write_text(
        "{}",
        encoding="utf-8",
    )

    legacy = tmp_path / ".repository-intelligence-platform"

    legacy.mkdir()

    (legacy / "project.json").write_text(
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

def test_scan_respects_gitignore(
    tmp_path: Path,
) -> None:
    """Indexing reads the scan, so ignored build output is never indexed."""

    from app.repository.scanner import RepositoryScanner

    (tmp_path / ".gitignore").write_text(
        "build/\n*.min.js\n",
        encoding="utf-8",
    )

    (tmp_path / "build").mkdir()

    (tmp_path / "build" / "out.py").write_text(
        "x = 1\n",
        encoding="utf-8",
    )

    (tmp_path / "app.min.js").write_text(
        "a()",
        encoding="utf-8",
    )

    (tmp_path / "app.js").write_text(
        "a()",
        encoding="utf-8",
    )

    paths = {
        entry.relative_path.as_posix()
        for entry in RepositoryScanner().scan(
            tmp_path,
        )
    }

    assert "app.js" in paths

    assert "build" not in paths

    assert "build/out.py" not in paths

    assert "app.min.js" not in paths


def test_pathological_gitignore_patterns_are_skipped_quickly(
    tmp_path: Path,
) -> None:
    """A hostile .gitignore cannot stall every walk (security review)."""

    import time

    from app.repository.ignore import RepositoryIgnoreRules

    (tmp_path / ".gitignore").write_text(
        "*a*a*a*a*a*a*a*a*b\nbuild/\n",
        encoding="utf-8",
    )

    rules = RepositoryIgnoreRules(
        tmp_path,
    )

    started = time.monotonic()

    long_name = tmp_path / ("a" * 200)

    assert not rules.is_ignored(long_name, is_directory=False)

    # The safe pattern on the next line still applies.
    assert rules.is_ignored(tmp_path / "build", is_directory=True)

    assert time.monotonic() - started < 1


def test_gitignore_with_bom_and_bad_pattern(
    tmp_path: Path,
) -> None:
    from app.repository.ignore import RepositoryIgnoreRules

    (tmp_path / ".gitignore").write_bytes(
        "\ufeffdist/\n".encode("utf-8"),
    )

    assert RepositoryIgnoreRules(tmp_path).is_ignored(
        tmp_path / "dist",
        is_directory=True,
    )
