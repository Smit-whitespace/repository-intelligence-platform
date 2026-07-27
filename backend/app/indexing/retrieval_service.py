"""Semantic retrieval service."""

from app.indexing.providers import EmbeddingProvider
from app.indexing.retrieval_models import (
    SearchHit,
    SearchQuery,
    SearchResponse,
    SearchResult,
)
from app.indexing.stores import VectorStore


class RetrievalService:
    """Semantic repository retrieval."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        """Initialize the retrieval service."""

        self._embedding_provider = embedding_provider

        self._vector_store = vector_store

    def search(
        self,
        query: SearchQuery,
    ) -> SearchResponse:
        """Perform semantic retrieval."""

        query_embedding = self._embedding_provider.embed(
            [
                query.query,
            ],
        )[0]

        search_hits = self._vector_store.search(
            query_embedding=query_embedding,
            limit=query.limit,
        )

        search_hits = self._deduplicate(
            search_hits,
        )

        search_results = [
            SearchResult(
                chunk_id=hit.chunk_id,
                content=hit.content,
                metadata=hit.metadata,
                boundary=hit.boundary,
                similarity_score=(
                    self._normalize_score(
                        hit.vector_score,
                    )
                ),
            )
            for hit in search_hits
        ]

        return SearchResponse(
            query=query.query,
            results=search_results,
        )

    @staticmethod
    def _normalize_score(
        distance: float,
    ) -> float:
        """Convert L2 distance to a heuristic ranking score.

        The formula ``1 / (1 + distance)`` produces a value in (0, 1]
        where higher means more relevant. This is **not** a calibrated
        cosine similarity — it is only safe to use as a relative ranking
        metric for results within a single query.
        """

        return 1.0 / (1.0 + distance)

    @staticmethod
    def _deduplicate(
        hits: list[SearchHit],
    ) -> list[SearchHit]:
        """Remove duplicate chunk_ids, keeping the lowest distance."""

        seen: dict[str, SearchHit] = {}

        for hit in hits:
            existing = seen.get(
                hit.chunk_id,
            )

            if existing is None or hit.vector_score < existing.vector_score:
                seen[hit.chunk_id] = hit

        return list(
            seen.values(),
        )
