"""Semantic retrieval service."""

from app.indexing.providers import EmbeddingProvider
from app.indexing.retrieval_models import (
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

        self._embedding_provider = (
            embedding_provider
        )

        self._vector_store = (
            vector_store
        )

    def search(
        self,
        query: SearchQuery,
    ) -> SearchResponse:
        """Perform semantic retrieval."""

        query_embedding = (
            self._embedding_provider.embed(
                [
                    query.query,
                ],
            )[0]
        )

        search_hits = (
            self._vector_store.search(
                query_embedding=query_embedding,
                limit=query.limit,
            )
        )

        search_results = [
            SearchResult(
                chunk_id=hit.chunk_id,
                content=hit.content,
                metadata=hit.metadata,
                boundary=hit.boundary,
                similarity_score=hit.vector_score,
            )
            for hit in search_hits
        ]

        return SearchResponse(
            query=query.query,
            results=search_results,
        )