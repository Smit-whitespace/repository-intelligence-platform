"""Indexing domain models."""

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from app.repository.models import (
    ChunkBoundary,
    RepositoryChunkMetadata,
)


class EmbeddingVector(BaseModel):
    """Embedding vector."""

    values: list[float]


class IndexedChunk(BaseModel):
    """Chunk ready for indexing."""

    chunk_id: str

    content: str

    metadata: RepositoryChunkMetadata

    boundary: ChunkBoundary

    embedding: EmbeddingVector


class FileFailureInfo(BaseModel):
    """Information about a single indexing failure."""

    relative_path: str

    stage: str

    exception_type: str

    message: str


class IndexingDiagnostics(BaseModel):
    """Repository indexing diagnostics."""

    total_files_discovered: int

    text_files_detected: int

    total_chunks_created: int

    indexing_duration_ms: int

    failed_files_details: list[FileFailureInfo]


class IndexingResult(BaseModel):
    """Repository indexing summary."""

    # Descriptions, not comments: they reach API and MCP schemas, where an
    # agent once added unchanged_files to indexed_files and got a total
    # one larger than scanned_files.

    scanned_files: int = Field(
        description="Files found: indexed_files + skipped_files + failed_files.",
    )

    indexed_files: int = Field(
        description=(
            "Files whose chunks are in the index after this run, including "
            "unchanged_files."
        ),
    )

    indexed_chunks: int = Field(
        description="Chunks embedded in this run (unchanged chunks are not counted).",
    )

    skipped_files: int = Field(
        description="Files not indexed by design: binary, lock files, or not text.",
    )

    failed_files: int = Field(
        description="Files that could not be indexed; they keep their previous chunks.",
    )

    unchanged_files: int = Field(
        default=0,
        description=(
            "Part of indexed_files: files whose content had not changed, so "
            "nothing was re-embedded for them."
        ),
    )

    diagnostics: IndexingDiagnostics | None = None


class FileUpdateResult(BaseModel):
    """Outcome of updating a given set of files in the index."""

    done: list[str] = Field(
        description="Files now in sync with the index (re-indexed, or removed because gone).",
    )

    remaining: list[str] = Field(
        description="Files not started because the deadline passed; still stale.",
    )

    failed: list[str] = Field(
        description="Files that could not be indexed; they keep their previous chunks.",
    )


class FreshnessState(StrEnum):
    """How a project's index compares with the files on disk."""

    UP_TO_DATE = "up_to_date"
    """Nothing changed since indexing."""

    UPDATED = "updated"
    """Every changed file was updated before answering."""

    PARTIAL = "partial"
    """Some changed files are not in the index yet (still updating, or failed)."""

    BUSY = "busy"
    """Another process holds the index lock; nothing was updated."""

    UPDATING = "updating"
    """This process is updating the index (``status`` only)."""

    STALE = "stale"
    """Files changed and nothing is updating them (``status`` only)."""

    OFF = "off"
    """Automatic updates are off; the change set is reported only."""

    NOT_INDEXED = "not_indexed"

    INCOMPATIBLE = "incompatible"
    """Built with a different embedding model; never updated automatically."""

    FAILED = "failed"
    """The freshness step itself failed; see the note."""


class FreshnessResult(BaseModel):
    """What the freshness step found and did for one project."""

    state: FreshnessState

    changed_files: int = Field(
        default=0,
        description="Indexed files whose content changed.",
    )

    added_files: int = Field(
        default=0,
        description="Files not in the index yet.",
    )

    removed_files: int = Field(
        default=0,
        description="Indexed files that are gone or no longer indexable.",
    )

    updated_files: int = Field(
        default=0,
        description="Files brought in sync with the index by this call.",
    )

    pending_files: int = Field(
        default=0,
        description="Changed files still not in the index after this call.",
    )

    seconds: float = Field(
        default=0.0,
        description="Time this call spent.",
    )

    note: str | None = Field(
        default=None,
        description="One line for the answer when it may miss changed files.",
    )


class RepositoryIndex(BaseModel):
    """Indexed repository."""

    repository_root: Path

    indexed_at: datetime

    result: IndexingResult


class IndexStatus(BaseModel):
    """Whether a project is indexed, and with which embedding model."""

    indexed: bool

    embedding_model: str | None = None
    """Model recorded in the index; None if unindexed or built before
    the model was recorded."""

    configured_embedding_model: str

    compatible: bool
    """True when searching the index with the configured model is valid.
    An index built before the model was recorded counts as compatible
    (it is rebuilt on the next indexing run)."""
