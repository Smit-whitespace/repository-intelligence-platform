"""Repository domain models."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class RepositoryEntry(BaseModel):
    """Repository filesystem entry."""

    name: str

    absolute_path: Path

    relative_path: Path

    is_directory: bool

    size_bytes: int | None = None

    modified_at: datetime | None = None


class RepositorySummary(BaseModel):
    """Repository summary."""

    files: int

    directories: int

    total_size_bytes: int


class RepositoryIndex(BaseModel):
    """Repository scan result."""

    summary: RepositorySummary

    entries: list[RepositoryEntry]