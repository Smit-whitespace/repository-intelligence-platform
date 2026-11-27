"""Storage directory names, and moving the former ``.local_openclaw``."""

import os
from pathlib import Path

import pytest

from app.core.storage.exceptions import StorageMigrationError
from app.core.storage.locations import (
    LEGACY_STORAGE_DIRECTORY_NAMES,
    PROJECT_STORAGE_DIRECTORY_NAME,
    PROTECTED_DIRECTORY_NAMES,
    project_storage_directory,
    user_storage_directory,
)
from app.repository.ignore import should_ignore


def _legacy_project(
    root: Path,
) -> Path:
    legacy = root / ".local_openclaw"
    (legacy / "snapshots").mkdir(parents=True)
    (legacy / "project.json").write_text('{"name": "demo"}', encoding="utf-8")
    (legacy / "snapshots" / "one.json").write_text("{}", encoding="utf-8")
    return legacy


def test_the_storage_directory_is_named_rip() -> None:
    assert PROJECT_STORAGE_DIRECTORY_NAME == ".rip"
    assert LEGACY_STORAGE_DIRECTORY_NAMES == (".local_openclaw",)


def test_a_legacy_project_directory_is_moved_with_its_contents(
    tmp_path: Path,
) -> None:
    legacy = _legacy_project(tmp_path)

    storage = project_storage_directory(tmp_path)

    assert storage == tmp_path.resolve() / ".rip"
    assert (storage / "project.json").read_text(encoding="utf-8") == '{"name": "demo"}'
    assert (storage / "snapshots" / "one.json").exists()
    assert not legacy.exists()


def test_a_project_without_storage_gets_nothing_created(
    tmp_path: Path,
) -> None:
    storage = project_storage_directory(tmp_path)

    assert storage == tmp_path.resolve() / ".rip"
    assert not storage.exists()


def test_an_existing_rip_directory_wins_and_the_legacy_one_is_left_alone(
    tmp_path: Path,
) -> None:
    legacy = _legacy_project(tmp_path)
    (tmp_path / ".rip").mkdir()
    (tmp_path / ".rip" / "project.json").write_text("{}", encoding="utf-8")

    storage = project_storage_directory(tmp_path)

    assert (storage / "project.json").read_text(encoding="utf-8") == "{}"
    assert (legacy / "project.json").exists()


def test_a_legacy_directory_that_is_a_link_is_not_moved(
    tmp_path: Path,
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    root = tmp_path / "project"
    root.mkdir()

    try:
        os.symlink(elsewhere, root / ".local_openclaw", target_is_directory=True)

    except OSError:
        pytest.skip("creating symlinks is not permitted here")

    storage = project_storage_directory(root)

    assert not storage.exists()
    assert (root / ".local_openclaw").is_symlink()


def test_a_failed_move_is_an_error_not_a_silent_fresh_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _legacy_project(tmp_path)

    def locked(
        self: Path,
        target: Path,
    ) -> Path:
        raise PermissionError("in use by another process")

    monkeypatch.setattr(Path, "rename", locked)

    with pytest.raises(StorageMigrationError, match="Close any other RIP"):
        project_storage_directory(tmp_path)


def test_the_user_directory_moves_too(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = tmp_path / ".local_openclaw"
    legacy.mkdir()
    (legacy / "integrity.key").write_text("abc", encoding="ascii")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    storage = user_storage_directory()

    assert storage == tmp_path / ".rip"
    assert (storage / "integrity.key").read_text(encoding="ascii") == "abc"
    assert not legacy.exists()


@pytest.mark.parametrize("name", [".rip", ".local_openclaw"])
def test_current_and_legacy_names_are_protected_and_never_indexed(
    name: str,
) -> None:
    assert name in PROTECTED_DIRECTORY_NAMES
    assert should_ignore(Path(name))
