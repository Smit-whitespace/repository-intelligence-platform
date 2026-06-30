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