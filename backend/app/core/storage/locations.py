"""Canonical project-local persistence locations.

The storage identity for a project derives exclusively from the project
root directory (an absolute, resolved path) — never from the process
working directory. Starting RIP from the repository root, ``backend/``,
an IDE, or any other terminal working directory therefore resolves the
same persistence location for the same opened project.

Canonical layout for a project rooted at ``<root>``::

    <root>/.rip/                project-local runtime storage
    <root>/.rip/project.json    project metadata
    <root>/.rip/index/chroma    vector index (ChromaDB)
    <root>/.rip/snapshots/      editing snapshots

Per-user files (the API token, the integrity key, ``models.json``) live
in ``~/.rip``.

``.rip`` is the single authoritative internal storage directory name.
Until Sprint 14 it was ``.local_openclaw``, from the project's working
title; a directory still under that name is moved the first time its
location is resolved (ADR-0021).
"""

import logging
import os
from pathlib import Path

from app.core.storage.exceptions import StorageMigrationError

logger = logging.getLogger(__name__)

PROJECT_STORAGE_DIRECTORY_NAME = ".rip"

LEGACY_STORAGE_DIRECTORY_NAMES = (".local_openclaw",)
"""Former names of the storage directory. They stay protected and never
indexed, so a copy left behind, or one that arrives with a cloned
repository, is never read as repository content."""

PROJECT_METADATA_FILE_NAME = "project.json"

INDEX_RELATIVE_DIRECTORY = Path("index")

CHROMA_RELATIVE_DIRECTORY = Path("index/chroma")

SNAPSHOTS_RELATIVE_DIRECTORY = Path("snapshots")

PROTECTED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        PROJECT_STORAGE_DIRECTORY_NAME,
        *LEGACY_STORAGE_DIRECTORY_NAMES,
    },
)
"""Directory names that repository tools never read from or write into.

``.git`` because writing ``.git/hooks/*`` is arbitrary code execution
(and its internals are noise to an agent); ``.rip`` (and its former
names) because it holds RIP's own index and the snapshots that rollback
depends on. Compared case-insensitively, because Windows and macOS file
systems are case-insensitive by default.
"""


def project_storage_directory(
    root_directory: str | Path,
) -> Path:
    """Return the canonical project-local storage directory.

    The path is derived from the resolved project root only and is
    independent of the process working directory. A storage directory
    still under a former name is moved into place first.
    """

    return _storage_directory(
        Path(root_directory).resolve(),
    )


def user_storage_directory() -> Path:
    """Return the per-user storage directory, ``~/.rip``.

    A directory still under a former name is moved into place first, so
    the API token, the integrity key and ``models.json`` carry over: a
    new integrity key would make every signed proposal and snapshot
    fail verification.
    """

    return _storage_directory(
        Path.home(),
    )


def _storage_directory(
    parent: Path,
) -> Path:
    """Return ``parent/.rip``, moving a former storage directory there.

    Done wherever the location is resolved rather than once at startup,
    so the app, the MCP server and every other entry point see the same
    folder whichever runs first. Once ``.rip`` exists this costs one
    ``stat``.
    """

    current = parent / PROJECT_STORAGE_DIRECTORY_NAME

    if os.path.lexists(current):
        return current

    for name in LEGACY_STORAGE_DIRECTORY_NAMES:
        legacy = parent / name

        # A link is not moved: RIP refuses linked storage anyway, and
        # renaming it would only carry the link to the new name.
        if legacy.is_dir() and not is_link(legacy):
            _move(
                legacy,
                current,
            )

            break

    return current


def _move(
    legacy: Path,
    current: Path,
) -> None:
    """Rename a former storage directory, or fail loudly.

    Carrying on without the old directory would mean a new index, lost
    rollback snapshots and, for the per-user directory, a new integrity
    key and API token.
    """

    try:
        legacy.rename(
            current,
        )

    except OSError as error:
        # Another RIP process may have moved it a moment earlier.
        if current.is_dir():
            return

        raise StorageMigrationError(
            f"RIP now keeps its data in {current}, and could not move "
            f"{legacy} there: {error}. Close any other RIP process using "
            f"it (the app or an MCP server) and try again, or rename the "
            f"folder yourself.",
        ) from error

    logger.info(
        "Moved %s to %s",
        legacy,
        current,
    )


def project_metadata_path(
    root_directory: str | Path,
) -> Path:
    """Return the project metadata file path."""

    return (
        project_storage_directory(root_directory)
        / PROJECT_METADATA_FILE_NAME
    )


def project_chroma_directory(
    root_directory: str | Path,
) -> Path:
    """Return the ChromaDB persist directory for a project."""

    return (
        project_storage_directory(root_directory)
        / CHROMA_RELATIVE_DIRECTORY
    )


def project_snapshots_directory(
    root_directory: str | Path,
) -> Path:
    """Return the editing snapshots directory for a project."""

    return (
        project_storage_directory(root_directory)
        / SNAPSHOTS_RELATIVE_DIRECTORY
    )


def is_registered_project(
    root_directory: str | Path,
) -> bool:
    """Return whether a directory is a registered RIP project.

    A project is registered once its metadata file exists. Tools that
    read or modify a repository only accept registered roots, so a
    caller cannot point them at an arbitrary directory.

    A storage directory or metadata file that is a symlink or junction is
    not accepted: RIP would then write its index and snapshots wherever
    the link points.
    """

    storage_directory = project_storage_directory(
        root_directory,
    )

    metadata_path = storage_directory / PROJECT_METADATA_FILE_NAME

    if is_link(storage_directory) or is_link(metadata_path):
        return False

    return metadata_path.is_file()


def is_link(
    path: Path,
) -> bool:
    """Return whether a path is a symlink or a Windows junction.

    ``Path.is_symlink`` is False for junctions, which Windows users can
    create without admin rights, so both must be checked.
    """

    return path.is_symlink() or path.is_junction()


def is_valid_path_text(
    path_text: str,
) -> bool:
    """Reject path text that the filesystem would misinterpret.

    NUL bytes make path functions raise. On Windows, ``:`` outside the
    drive prefix addresses an alternate data stream (``file.txt:hidden``),
    which no repository file legitimately uses.
    """

    if "\x00" in path_text:
        return False

    return os.name != "nt" or ":" not in path_text


def is_protected_path(
    relative_path: Path,
) -> bool:
    """Return whether a repository-relative path is in a protected directory."""

    return any(
        part.casefold() in PROTECTED_DIRECTORY_NAMES
        for part in relative_path.parts
    )
