"""Indexing domain models."""

from datetime import datetime
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
