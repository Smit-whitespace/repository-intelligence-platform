"""Tests for retrieval service."""

from pathlib import Path
from unittest.mock import MagicMock

from app.indexing.providers import EmbeddingProvider
from app.indexing.retrieval_models import (
    SearchHit,
    SearchQuery,
    SearchResult,
)
from app.indexing.retrieval_service import (
    RetrievalService,
)
from app.indexing.store_resolver import StaticVectorStoreResolver
from app.indexing.stores import VectorStore
from app.repository.models import (
    ChunkBoundary,
    ChunkType,
    RepositoryChunkMetadata,
)
from app.indexing.models import (
    EmbeddingVector,
)


def create_hit(
    chunk_id: str = "chunk-1",
    distance: float = 0.5,
    path: str | None = None,
) -> SearchHit:
    """Create a sample search hit (in its own file unless ``path`` is given)."""

    return SearchHit(
        chunk_id=chunk_id,
        content="def main():\n    pass",
        metadata=RepositoryChunkMetadata(
            relative_path=Path(path or f"src/{chunk_id}.py"),
            language="python",
            mime_type="text/x-python",
            sha256="abc123",
        ),
        boundary=ChunkBoundary(
            start_line=1,
            end_line=2,
            chunk_type=ChunkType.FUNCTION,
        ),
        vector_score=distance,
    )


def create_service() -> tuple[
    RetrievalService,
    MagicMock,
    MagicMock,
]:
    """Create a retrieval service with mocked dependencies."""

    embedding_provider = MagicMock(
        spec=EmbeddingProvider,
    )

    vector_store = MagicMock(
        spec=VectorStore,
    )

    # A spec'd mock would return a truthy MagicMock here; ``None`` is the
    # "store does not track index metadata" contract.
    vector_store.get_index_metadata.return_value = None

    service = RetrievalService(
        embedding_provider=embedding_provider,
        vector_store_resolver=StaticVectorStoreResolver(
            vector_store,
        ),
    )

    return (
        service,
        embedding_provider,
        vector_store,
    )


def make_query(
    query: str = "test",
    *,
    limit: int = 10,
) -> SearchQuery:
    """Create a project-scoped search query."""

    return SearchQuery(
        query=query,
        root_directory="/projects/foo",
        limit=limit,
    )


class TestSearch:
    """Tests for RetrievalService.search()."""

    def test_returns_search_response(
        self,
    ) -> None:
        """Search should return a SearchResponse."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(),
        ]

        result = service.search(
            make_query(),
        )

        assert result.query == "test"

        assert len(result.results) == 1

        assert isinstance(
            result.results[0],
            SearchResult,
        )

    def test_normalizes_scores(
        self,
    ) -> None:
        """Search should convert distance to a 0-1 similarity score."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(
                chunk_id="chunk-1",
                distance=0.0,
            ),
            create_hit(
                chunk_id="chunk-2",
                distance=1.0,
            ),
            create_hit(
                chunk_id="chunk-3",
                distance=4.0,
            ),
        ]

        result = service.search(
            make_query(),
        )

        assert len(result.results) == 3

        assert result.results[0].similarity_score == 1.0

        assert result.results[1].similarity_score == 0.5

        assert result.results[2].similarity_score == 0.2

    def test_ranks_from_a_larger_pool_and_returns_at_most_limit(
        self,
    ) -> None:
        """Ranking needs more candidates than it returns."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(chunk_id=f"c{i}", distance=i / 10)
            for i in range(20)
        ]

        result = service.search(
            make_query(
                limit=5,
            ),
        )

        store.search.assert_called_once()

        assert store.search.call_args[1]["limit"] >= 50

        assert len(result.results) == 5

    def test_shows_each_file_once_with_its_best_chunk(
        self,
    ) -> None:
        """Repeated chunks of one file used to fill the results, leaving
        room for fewer files (2.6 of 10 slots on this repository)."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(chunk_id="a-best", distance=0.1, path="app/a.py"),
            create_hit(chunk_id="a-second", distance=0.2, path="app/a.py"),
            create_hit(chunk_id="b", distance=0.3, path="app/b.py"),
        ]

        result = service.search(
            make_query(),
        )

        assert [r.chunk_id for r in result.results] == [
            "a-best",
            "b",
        ]

    def test_test_files_rank_below_equally_close_source(
        self,
    ) -> None:
        """Tests describe the same behavior in the same words and used to
        outrank the code they test."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(chunk_id="test", distance=0.50, path="backend/tests/test_pricing.py"),
            create_hit(chunk_id="spec", distance=0.51, path="frontend/src/a.test.ts"),
            create_hit(chunk_id="source", distance=0.55, path="app/pricing.py"),
        ]

        result = service.search(
            make_query(),
        )

        assert result.results[0].chunk_id == "source"

    def test_a_much_closer_test_file_still_ranks_first(
        self,
    ) -> None:
        """The penalty demotes tests; it does not hide them."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(chunk_id="test", distance=0.10, path="tests/test_pricing.py"),
            create_hit(chunk_id="source", distance=0.90, path="app/pricing.py"),
        ]

        result = service.search(
            make_query(),
        )

        assert result.results[0].chunk_id == "test"

    def test_passes_where_filter_when_root_directory_set(
        self,
    ) -> None:
        """Search should forward the where filter when root_directory is set."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(),
        ]

        service.search(
            SearchQuery(
                query="test",
                root_directory="/projects/foo",
            ),
        )

        store.search.assert_called_once()

        assert store.search.call_args[1]["where"] == {
            "root_directory": "/projects/foo",
        }

    def test_search_skips_store_without_root_directory(
        self,
    ) -> None:
        """Search without a project root never touches a store."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(),
        ]

        result = service.search(
            SearchQuery(query="test"),
        )

        assert result.results == []

        store.search.assert_not_called()

    def test_embeds_query(
        self,
    ) -> None:
        """Search should embed the query text."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(),
        ]

        service.search(
            make_query(query="find main function"),
        )

        provider.embed.assert_called_once_with(
            [
                "find main function",
            ],
        )

    def test_returns_empty_results(
        self,
    ) -> None:
        """Search should return empty list when store has no results."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = []

        result = service.search(
            make_query(),
        )

        assert result.results == []

    def test_preserves_result_order(
        self,
    ) -> None:
        """Search should preserve the relevance order from the store."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(
                chunk_id="chunk-best",
                distance=0.1,
            ),
            create_hit(
                chunk_id="chunk-good",
                distance=0.5,
            ),
            create_hit(
                chunk_id="chunk-ok",
                distance=0.9,
            ),
        ]

        result = service.search(
            make_query(),
        )

        assert [r.chunk_id for r in result.results] == [
            "chunk-best",
            "chunk-good",
            "chunk-ok",
        ]

        assert (
            result.results[0].similarity_score
            > result.results[1].similarity_score
            > result.results[2].similarity_score
        )

    def test_retrieves_mjs_chunks(
        self,
    ) -> None:
        """Retrieval should return .mjs chunks with correct metadata."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0],
            ),
        ]

        store.search.return_value = [
            SearchHit(
                chunk_id="mjs-chunk",
                content="export const VERSION = '1.0.0';",
                metadata=RepositoryChunkMetadata(
                    relative_path=Path(
                        "module.mjs",
                    ),
                    language="JavaScript",
                    mime_type="text/javascript",
                    sha256="abc123",
                ),
                boundary=ChunkBoundary(
                    start_line=1,
                    end_line=1,
                    chunk_type=ChunkType.GENERIC,
                ),
                vector_score=0.5,
            ),
        ]

        result = service.search(
            make_query(),
        )

        assert len(
            result.results,
        ) == 1

        hit = result.results[0]

        assert (
            hit.metadata.relative_path
            == Path("module.mjs")
        )

        assert (
            hit.metadata.language
            == "JavaScript"
        )

        assert (
            hit.metadata.mime_type
            == "text/javascript"
        )

        assert (
            hit.metadata.sha256 == "abc123"
        )

    def test_retrieves_cjs_chunks(
        self,
    ) -> None:
        """Retrieval should return .cjs chunks with correct metadata."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0],
            ),
        ]

        store.search.return_value = [
            SearchHit(
                chunk_id="cjs-chunk",
                content="module.exports = {};",
                metadata=RepositoryChunkMetadata(
                    relative_path=Path(
                        "config.cjs",
                    ),
                    language="JavaScript",
                    mime_type="text/javascript",
                    sha256="def456",
                ),
                boundary=ChunkBoundary(
                    start_line=1,
                    end_line=1,
                    chunk_type=ChunkType.GENERIC,
                ),
                vector_score=0.5,
            ),
        ]

        result = service.search(
            make_query(),
        )

        assert len(
            result.results,
        ) == 1

        hit = result.results[0]

        assert (
            hit.metadata.relative_path
            == Path("config.cjs")
        )

        assert (
            hit.metadata.language
            == "JavaScript"
        )

        assert (
            hit.metadata.mime_type
            == "text/javascript"
        )

        assert (
            hit.metadata.sha256 == "def456"
        )


class TestDeduplication:
    """Tests for duplicate chunk_id removal."""

    def test_removes_duplicate_chunk_ids(
        self,
    ) -> None:
        """Deduplicate should keep only the lowest distance per chunk_id."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = [
            create_hit(
                chunk_id="chunk-1",
                distance=0.9,
            ),
            create_hit(
                chunk_id="chunk-1",
                distance=0.1,
            ),
            create_hit(
                chunk_id="chunk-2",
                distance=0.5,
            ),
        ]

        result = service.search(
            make_query(),
        )

        chunk_ids = [r.chunk_id for r in result.results]

        assert chunk_ids == [
            "chunk-1",
            "chunk-2",
        ]

        chunk_1_result = next(r for r in result.results if r.chunk_id == "chunk-1")

        expected = 1.0 / (1.0 + 0.1)

        assert chunk_1_result.similarity_score == expected

    def test_preserves_unique_chunks(
        self,
    ) -> None:
        """Deduplicate should not change unique chunk_ids."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        hits = [
            create_hit(
                chunk_id="chunk-1",
                distance=0.1,
            ),
            create_hit(
                chunk_id="chunk-2",
                distance=0.5,
            ),
            create_hit(
                chunk_id="chunk-3",
                distance=0.9,
            ),
        ]

        store.search.return_value = hits

        result = service.search(
            make_query(),
        )

        assert len(result.results) == 3

        assert [r.chunk_id for r in result.results] == [
            "chunk-1",
            "chunk-2",
            "chunk-3",
        ]

    def test_empty_list(
        self,
    ) -> None:
        """Deduplicate should handle empty input."""

        service, provider, store = create_service()

        provider.embed.return_value = [
            EmbeddingVector(
                values=[1.0, 2.0, 3.0],
            ),
        ]

        store.search.return_value = []

        result = service.search(
            make_query(),
        )

        assert result.results == []


class TestNormalizeScore:
    """Tests for score normalization."""

    def test_perfect_match(
        self,
    ) -> None:
        """Zero distance should yield 1.0 similarity."""

        assert (
            RetrievalService._normalize_score(
                0.0,
            )
            == 1.0
        )

    def test_distance_one(
        self,
    ) -> None:
        """Distance of 1.0 should yield 0.5 similarity."""

        assert (
            RetrievalService._normalize_score(
                1.0,
            )
            == 0.5
        )

    def test_large_distance(
        self,
    ) -> None:
        """Large distance should approach 0 similarity."""

        assert (
            RetrievalService._normalize_score(
                100.0,
            )
            < 0.02
        )
