"""Canonical project-local persistence locations.

The storage identity for a project derives exclusively from the project
root directory (an absolute, resolved path) — never from the process
working directory. Starting RIP from the repository root, ``backend/``,
an IDE, or any other terminal working directory therefore resolves the
same persistence location for the same opened project.

Canonical layout for a project rooted at ``<root>``::

    <root>/.local_openclaw/                project-local runtime storage
    <root>/.local_openclaw/project.json    project metadata
    <root>/.local_openclaw/index/chroma    vector index (ChromaDB)
    <root>/.local_openclaw/snapshots/      editing snapshots

``.local_openclaw`` is the single authoritative internal storage
directory name. No competing names (``.repository-intelligence-platform``,
``.local_rip``, ``.rip``) are used for the same purpose.
"""

from pathlib import Path

PROJECT_STORAGE_DIRECTORY_NAME = ".local_openclaw"

PROJECT_METADATA_FILE_NAME = "project.json"

INDEX_RELATIVE_DIRECTORY = Path("index")

CHROMA_RELATIVE_DIRECTORY = Path("index/chroma")

SNAPSHOTS_RELATIVE_DIRECTORY = Path("snapshots")


def project_storage_directory(
    root_directory: str | Path,
) -> Path:
    """Return the canonical project-local storage directory.

    The path is derived from the resolved project root only and is
    independent of the process working directory.
    """

    return (
        Path(root_directory).resolve()
        / PROJECT_STORAGE_DIRECTORY_NAME
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
