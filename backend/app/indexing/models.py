"""Indexing domain models."""

from pydantic import BaseModel
from datetime import datetime
from pathlib import Path


class EmbeddingVector(BaseModel):
    """Embedding vector."""

    values: list[float]


class IndexedChunk(BaseModel):
    """Chunk ready for indexing."""

    chunk_id: str

    text: str

    embedding: EmbeddingVector


class IndexingResult(BaseModel):
    """Repository indexing summary."""

    scanned_files: int

    indexed_files: int

    indexed_chunks: int

    skipped_files: int

    failed_files: int

class RepositoryIndex(BaseModel):
    """Indexed repository."""

    repository_root: Path

    indexed_at: datetime

    result: IndexingResult