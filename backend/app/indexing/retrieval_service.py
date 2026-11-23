"""Semantic retrieval service."""

import logging

from app.indexing.exceptions import IndexIncompatibleError
from app.indexing.providers import EmbeddingProvider
from app.indexing.retrieval_models import (
    SearchHit,
    SearchQuery,
    SearchResponse,
    SearchResult,
)
from app.indexing.store_resolver import VectorStoreResolver
from app.indexing.stores import (
    EMBEDDING_MODEL_METADATA_KEY,
    VectorStore,
)

logger = logging.getLogger(__name__)


class RetrievalService:
    """Semantic repository retrieval.

    Retrieval is scoped to the project identified by
    ``SearchQuery.root_directory``. The vector store is resolved from
    the project root so retrieval never depends on the process working
    directory. A query without a project root (no project opened) and a
    project that has never been indexed both return no results.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store_resolver: VectorStoreResolver,
    ) -> None:
        """Initialize the retrieval service."""

        self._embedding_provider = embedding_provider

        self._vector_store_resolver = vector_store_resolver

    def search(
        self,
        query: SearchQuery,
    ) -> SearchResponse:
        """Perform semantic retrieval."""

        if not query.root_directory:
            return SearchResponse(
                query=query.query,
                results=[],
            )

        vector_store = self._vector_store_resolver.for_project(
            query.root_directory,
        )

        if vector_store is None:
            return SearchResponse(
                query=query.query,
                results=[],
            )

        self._ensure_compatible(
            vector_store=vector_store,
            root_directory=query.root_directory,
        )

        query_embedding = self._embedding_provider.embed(
            [
                query.query,
            ],
        )[0]

        where = {"root_directory": query.root_directory}

        search_hits = vector_store.search(
            query_embedding=query_embedding,
            limit=query.limit,
            where=where,
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

    def _ensure_compatible(
        self,
        vector_store: VectorStore,
        root_directory: str,
    ) -> None:
        """Refuse to search an index built by another embedding model.

        Never falls back silently: a mismatch is an explicit error that
        names both models and the fix. An index built before the model
        was recorded is still searched (it is rebuilt on the next
        indexing run), with a warning.
        """

        metadata = vector_store.get_index_metadata()

        if metadata is None:
            return

        built_with = metadata.get(
            EMBEDDING_MODEL_METADATA_KEY,
        )

        configured = self._embedding_provider.identity

        if built_with is None:
            logger.warning(
                "Index for %s does not record its embedding model; "
                "reindex the project to enable compatibility checks.",
                root_directory,
            )
            return

        if built_with != configured:
            raise IndexIncompatibleError(
                f"This project's index was built with embedding model "
                f"'{built_with}', but the configured embedding model is "
                f"'{configured}'. Reindex the project to search it with "
                f"'{configured}'.",
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
