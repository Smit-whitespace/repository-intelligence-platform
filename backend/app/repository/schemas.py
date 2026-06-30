"""Repository API schemas."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class RepositoryEntryResponse(BaseModel):
    """Repository entry response."""

    name: str

    relative_path: Path

    is_directory: bool

    size_bytes: int | None

    modified_at: datetime | None

    language: str | None

    sha256: str | None 

    is_text_file: bool | None

    mime_type: str | None


class RepositorySummaryResponse(BaseModel):
    """Repository summary response."""

    files: int

    directories: int

    total_size_bytes: int


class RepositoryIndexResponse(BaseModel):
    """Repository index response."""

    summary: RepositorySummaryResponse

    entries: list[RepositoryEntryResponse]