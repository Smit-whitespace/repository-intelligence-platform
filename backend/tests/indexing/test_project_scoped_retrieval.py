"""Integration tests for project-scoped retrieval isolation."""

from collections.abc import Sequence
from pathlib import Path
from unittest.mock import MagicMock

from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.indexing.providers import EmbeddingProvider
from app.indexing.retrieval_models import (
    SearchHit,
    SearchQuery,
)
from app.indexing.retrieval_service import (
    RetrievalService,
)
from app.indexing.stores import VectorStore
from app.repository.models import (
    ChunkBoundary,
    ChunkType,
    RepositoryChunkMetadata,
)


class FakeFilteringVectorStore(VectorStore):
    """In-memory vector store that enforces where filters."""

    def __init__(
        self,
    ) -> None:
        self._chunks: dict[
            str,
            IndexedChunk,
        ] = {}

    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        for chunk in chunks:
            self._chunks[
                chunk.chunk_id
            ] = chunk

    def search(
        self,
        query_embedding: EmbeddingVector,
        limit: int = 10,
        where: dict | None = None,
    ) -> list[SearchHit]:
        matching: list[
            IndexedChunk
        ] = []

        for chunk in self._chunks.values():
            if where:
                metadata = (
                    chunk.metadata.model_dump(
                        mode="json",
                    )
                )
                if all(
                    metadata.get(k) == v
                    for k, v in where.items()
                ):
                    matching.append(
                        chunk,
                    )
            else:
                matching.append(chunk)

        return [
            SearchHit(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                metadata=chunk.metadata,
                boundary=chunk.boundary,
                vector_score=0.5,
            )
            for chunk in matching[:limit]
        ]

    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        for cid in chunk_ids:
            self._chunks.pop(
                cid,
                None,
            )

    def clear(
        self,
    ) -> None:
        self._chunks.clear()


REPO_A = "/projects/alpha"
REPO_B = "/projects/beta"


def make_chunk(
    chunk_id: str,
    root_directory: str,
) -> IndexedChunk:
    """Create an indexed chunk scoped to a root directory."""

    return IndexedChunk(
        chunk_id=chunk_id,
        content=f"content of {chunk_id}",
        metadata=RepositoryChunkMetadata(
            relative_path=Path(
                "file.py",
            ),
            language="python",
            mime_type="text/x-python",
            sha256="abc",
            root_directory=root_directory,
        ),
        boundary=ChunkBoundary(
            start_line=1,
            end_line=1,
            chunk_type=ChunkType.FUNCTION,
        ),
        embedding=EmbeddingVector(
            values=[1.0],
        ),
    )


def make_retrieval_service(
    store: VectorStore,
) -> tuple[
    RetrievalService,
    MagicMock,
]:
    """Create retrieval service with a given store."""

    provider = MagicMock(
        spec=EmbeddingProvider,
    )
    provider.embed.return_value = [
        EmbeddingVector(
            values=[1.0],
        ),
    ]

    service = RetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    return service, provider


class TestProjectScopedRetrieval:
    """Regression tests for project-scoped retrieval isolation."""

    def test_unscoped_search_returns_all_projects(
        self,
    ) -> None:
        """Search without root_directory should return chunks from all repos."""

        store = FakeFilteringVectorStore()
        store.add(
            [
                make_chunk(
                    "a-1",
                    REPO_A,
                ),
                make_chunk(
                    "b-1",
                    REPO_B,
                ),
            ],
        )

        service, _ = make_retrieval_service(
            store,
        )
        result = service.search(
            SearchQuery(query="test"),
        )

        assert {
            r.chunk_id
            for r in result.results
        } == {
            "a-1",
            "b-1",
        }

    def test_scoped_search_isolates_repository(
        self,
    ) -> None:
        """Search with root_directory should return only that repo's chunks."""

        store = FakeFilteringVectorStore()
        store.add(
            [
                make_chunk(
                    "a-1",
                    REPO_A,
                ),
                make_chunk(
                    "a-2",
                    REPO_A,
                ),
                make_chunk(
                    "b-1",
                    REPO_B,
                ),
                make_chunk(
                    "b-2",
                    REPO_B,
                ),
            ],
        )

        service, _ = make_retrieval_service(
            store,
        )

        result_a = service.search(
            SearchQuery(
                query="test",
                root_directory=REPO_A,
            ),
        )
        result_b = service.search(
            SearchQuery(
                query="test",
                root_directory=REPO_B,
            ),
        )

        assert {
            r.chunk_id
            for r in result_a.results
        } == {
            "a-1",
            "a-2",
        }

        assert {
            r.chunk_id
            for r in result_b.results
        } == {
            "b-1",
            "b-2",
        }

        assert not any(
            r.chunk_id.startswith("b-")
            for r in result_a.results
        )

        assert not any(
            r.chunk_id.startswith("a-")
            for r in result_b.results
        )

    def test_switching_repositories(
        self,
    ) -> None:
        """Searching repo A then repo B should produce correct results."""

        store = FakeFilteringVectorStore()
        store.add(
            [
                make_chunk(
                    "a-1",
                    REPO_A,
                ),
                make_chunk(
                    "b-1",
                    REPO_B,
                ),
            ],
        )

        service, _ = make_retrieval_service(
            store,
        )

        result_a = service.search(
            SearchQuery(
                query="test",
                root_directory=REPO_A,
            ),
        )
        assert [r.chunk_id for r in result_a.results] == [
            "a-1"
        ]

        result_b = service.search(
            SearchQuery(
                query="test",
                root_directory=REPO_B,
            ),
        )
        assert [r.chunk_id for r in result_b.results] == [
            "b-1"
        ]

        result_a_again = service.search(
            SearchQuery(
                query="test",
                root_directory=REPO_A,
            ),
        )
        assert [r.chunk_id for r in result_a_again.results] == [
            "a-1"
        ]

    def test_zero_results_on_unknown_repo(
        self,
    ) -> None:
        """Search with a root_directory that has no indexed chunks returns empty."""

        store = FakeFilteringVectorStore()
        store.add(
            [
                make_chunk(
                    "a-1",
                    REPO_A,
                ),
            ],
        )

        service, _ = make_retrieval_service(
            store,
        )

        result = service.search(
            SearchQuery(
                query="test",
                root_directory="/projects/unknown",
            ),
        )

        assert result.results == []

    def test_zero_results_when_store_returns_empty(
        self,
    ) -> None:
        """Empty store with root_directory filter returns empty."""

        store = FakeFilteringVectorStore()
        service, _ = make_retrieval_service(
            store,
        )

        result = service.search(
            SearchQuery(
                query="test",
                root_directory=REPO_A,
            ),
        )

        assert result.results == []
