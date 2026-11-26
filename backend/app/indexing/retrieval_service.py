"""Semantic retrieval service."""

import logging
import re

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

TEST_FILE_WEIGHT = 0.92
"""Multiplier on a test file's score. Chosen with ``python -m eval``:
0.90-0.94 scored the same on both question sets; 0.92 is the middle."""

CANDIDATE_POOL_FACTOR = 5

MIN_CANDIDATE_POOL = 50

MAX_CANDIDATE_POOL = 200


def _is_test_path(
    path: str,
) -> bool:
    """Whether a repository path is a test file.

    Matches a ``tests``/``test``/``__tests__`` directory and the usual
    file names: ``test_*.py``, ``*_test.py``, ``*.test.ts``, ``*.spec.js``.
    """

    parts = re.split(
        r"[\\/]",
        path.lower(),
    )

    name = parts[-1]

    return (
        any(
            part in {"tests", "test", "__tests__"}
            for part in parts[:-1]
        )
        or name.startswith("test_")
        or re.search(
            r"(_test\.py|\.(test|spec)\.[cm]?[jt]sx?)$",
            name,
        )
        is not None
    )


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

        # Rank from a larger pool than is returned, so that showing each
        # file once still fills the results.
        search_hits = vector_store.search(
            query_embedding=query_embedding,
            limit=min(
                max(
                    query.limit * CANDIDATE_POOL_FACTOR,
                    MIN_CANDIDATE_POOL,
                ),
                MAX_CANDIDATE_POOL,
            ),
            where=where,
        )

        search_hits = self._deduplicate(
            search_hits,
        )

        return SearchResponse(
            query=query.query,
            results=self._rank(
                search_hits,
                limit=query.limit,
            ),
        )

    def _rank(
        self,
        hits: list[SearchHit],
        limit: int,
    ) -> list[SearchResult]:
        """Order hits for people and agents, best first.

        Measured with ``python -m eval`` on this repository (tuning set
        and a held-out set; see docs/architecture/backend/retrieval.md):

        - Test files score ``TEST_FILE_WEIGHT`` times their similarity.
          They describe the same behavior in the same words and used to
          outrank the code they test; a much closer test still wins.
        - Each file appears once, with its best chunk, so ten results
          show ten files instead of several chunks of a few.
        """

        scored = sorted(
            (
                (
                    self._normalize_score(
                        hit.vector_score,
                    )
                    * (
                        TEST_FILE_WEIGHT
                        if _is_test_path(
                            str(
                                hit.metadata.relative_path,
                            ),
                        )
                        else 1.0
                    ),
                    hit,
                )
                for hit in hits
            ),
            key=lambda pair: -pair[0],
        )

        results: list[SearchResult] = []

        seen_files: set[str] = set()

        for score, hit in scored:
            path = str(
                hit.metadata.relative_path,
            )

            if path in seen_files:
                continue

            seen_files.add(
                path,
            )

            results.append(
                SearchResult(
                    chunk_id=hit.chunk_id,
                    content=hit.content,
                    metadata=hit.metadata,
                    boundary=hit.boundary,
                    similarity_score=score,
                ),
            )

            if len(results) == limit:
                break

        return results

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
