"""Indexing domain models."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

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

    scanned_files: int

    indexed_files: int

    indexed_chunks: int

    skipped_files: int

    failed_files: int

    diagnostics: IndexingDiagnostics | None = None


class RepositoryIndex(BaseModel):
    """Indexed repository."""

    repository_root: Path

    indexed_at: datetime

    result: IndexingResult
