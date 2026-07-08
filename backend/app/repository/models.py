"""Repository domain models."""

from datetime import datetime
from enum import StrEnum
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

    language: str | None = None

    sha256: str | None = None

    is_text_file: bool | None = None

    mime_type: str | None = None


class RepositorySummary(BaseModel):
    """Repository summary."""

    files: int

    directories: int

    total_size_bytes: int


class RepositoryIndex(BaseModel):
    """Repository scan result."""

    summary: RepositorySummary

    entries: list[RepositoryEntry]


class RepositoryManifest(BaseModel):
    """Repository manifest."""

    files: list[RepositoryEntry]

    directories: list[RepositoryEntry]


class RepositoryDocument(BaseModel):
    """Loaded repository document."""

    entry: RepositoryEntry

    content: str

    line_count: int


class RepositoryChunkMetadata(BaseModel):
    """Repository chunk metadata."""

    relative_path: Path

    language: str | None

    mime_type: str | None

    sha256: str


class ChunkType(StrEnum):
    """Repository chunk type."""

    GENERIC = "generic"

    MODULE = "module"

    CLASS = "class"

    FUNCTION = "function"

    ASYNC_FUNCTION = "async_function"


class ChunkBoundary(BaseModel):
    """Chunk line boundaries."""

    start_line: int

    end_line: int

    chunk_type: ChunkType = ChunkType.GENERIC


class RepositoryChunk(BaseModel):
    """Repository document chunk."""

    chunk_id: str

    entry: RepositoryEntry

    metadata: RepositoryChunkMetadata

    boundary: ChunkBoundary

    content: str