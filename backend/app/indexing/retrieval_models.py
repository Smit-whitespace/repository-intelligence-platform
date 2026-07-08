"""Semantic retrieval domain models."""

from pydantic import BaseModel

from app.repository.models import (
    ChunkBoundary,
    RepositoryChunkMetadata,
)


class SearchQuery(BaseModel):
    """Semantic search request."""

    query: str

    limit: int = 10


class SearchHit(BaseModel):
    """Candidate returned from vector search."""

    chunk_id: str

    content: str

    metadata: RepositoryChunkMetadata

    boundary: ChunkBoundary

    vector_score: float


class SearchResult(BaseModel):
    """Semantic search result."""

    chunk_id: str

    content: str

    metadata: RepositoryChunkMetadata

    boundary: ChunkBoundary

    similarity_score: float


class SearchResponse(BaseModel):
    """Semantic search response."""

    query: str

    results: list[SearchResult]