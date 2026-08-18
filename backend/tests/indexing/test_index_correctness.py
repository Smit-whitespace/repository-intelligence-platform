"""Index correctness tests (Sprint 13).

These tests reproduce the failure modes fixed in Sprint 13:

- chunk metadata must carry one canonical repository identity that
  survives equivalent (non-canonical) path spellings,
- re-indexing must invalidate stale chunks from modified and deleted
  files without accumulating obsolete rows,
- switching between repositories must not contaminate retrieval scopes.
"""

from collections.abc import Sequence
from pathlib import Path

from app.indexing.indexer import RepositoryIndexer
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.indexing.providers import EmbeddingProvider
from app.indexing.retrieval_models import SearchHit
from app.indexing.service import IndexingService
from app.indexing.store_resolver import StaticVectorStoreResolver
from app.indexing.stores import VectorStore
from app.projects.initialization_service import (
    ProjectInitializationService,
)
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService
from app.repository.chunking import RepositoryChunker
from app.repository.documents import (
    RepositoryDocumentLoader,
)
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import (
    ChunkBoundary,
    RepositoryChunkMetadata,
)
from app.repository.scanner import RepositoryScanner
from app.repository.service import RepositoryService


class FakeEmbeddingProvider(
    EmbeddingProvider,
):
    """Fake embedding provider."""

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Return deterministic embeddings."""

        return [
            EmbeddingVector(
                values=[1.0],
            )
            for _ in texts
        ]


class FakeVectorStore(
    VectorStore,
):
    """In-memory store mimicking Chroma semantics.

    ``add`` ignores ids that already exist (like Chroma), and
    ``get_chunk_ids``/``delete`` operate on the persisted rows only.
    """

    def __init__(
        self,
    ) -> None:
        """Initialize fake vector store."""

        self._chunks: dict[
            str,
            IndexedChunk,
        ] = {}

    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """Store indexed chunks, ignoring existing ids."""

        for chunk in chunks:
            if chunk.chunk_id not in self._chunks:
                self._chunks[chunk.chunk_id] = chunk

    def search(
        self,
        query_embedding: EmbeddingVector,
        limit: int = 10,
        where: dict | None = None,
    ) -> list[SearchHit]:
        """Return matching indexed chunks."""

        return []

    def get_chunk_ids(
        self,
        where: dict | None = None,
    ) -> list[str]:
        """Return ids of chunks matching the filter."""

        return [
            chunk.chunk_id
            for chunk in self._chunks.values()
            if self._matches(
                chunk,
                where,
            )
        ]

    @staticmethod
    def _matches(
        chunk: IndexedChunk,
        where: dict | None,
    ) -> bool:
        """Return whether a chunk matches the filter."""

        if where is None:
            return True

        metadata = chunk.metadata.model_dump(
            mode="json",
        )

        return all(metadata.get(key) == value for key, value in where.items())

    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        """Delete chunks."""

        for chunk_id in chunk_ids:
            self._chunks.pop(
                chunk_id,
                None,
            )

    def clear(
        self,
    ) -> None:
        """Remove all indexed chunks."""

        self._chunks.clear()

    def chunk_ids_by_file(
        self,
        file_name: str,
    ) -> set[str]:
        """Return ids of chunks whose source file name matches."""

        return {
            chunk.chunk_id
            for chunk in self._chunks.values()
            if chunk.metadata.relative_path.name == file_name
        }


def make_indexing_service(
    store: FakeVectorStore,
) -> IndexingService:
    """Create an indexing service with real pipeline components."""

    return IndexingService(
        scanner=RepositoryScanner(),
        metadata_extractor=RepositoryMetadataExtractor(),
        document_loader=RepositoryDocumentLoader(),
        chunker=RepositoryChunker(),
        indexer=RepositoryIndexer(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store_resolver=StaticVectorStoreResolver(
                store,
            ),
        ),
    )


def non_canonical_spelling(
    path: Path,
) -> Path:
    """Return an equivalent path spelling that differs from the canonical form."""

    return path / ".." / path.name


class TestCanonicalRepositoryIdentity:
    """Chunk metadata must use one canonical repository identity."""

    def test_chunk_metadata_uses_canonical_root_directory(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "main.py").write_text(
            "def main():\n    print('hello')",
            encoding="utf-8",
        )

        store = FakeVectorStore()

        service = make_indexing_service(
            store,
        )

        raw_path = non_canonical_spelling(
            tmp_path,
        )

        assert str(raw_path) != str(tmp_path.resolve())

        service.index_repository(
            raw_path,
        )

        canonical = str(
            tmp_path.resolve(),
        )

        assert store.chunk_ids_by_file(
            "main.py",
        )

        assert all(
            chunk.metadata.root_directory == canonical
            for chunk in store._chunks.values()
        )

    def test_retrieval_scope_matches_canonical_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "main.py").write_text(
            "x = 1",
            encoding="utf-8",
        )

        store = FakeVectorStore()

        service = make_indexing_service(
            store,
        )

        service.index_repository(
            non_canonical_spelling(
                tmp_path,
            ),
        )

        canonical = str(
            tmp_path.resolve(),
        )

        assert store.get_chunk_ids(
            where={
                "root_directory": canonical,
            },
        ) == list(
            store._chunks.keys(),
        )

    def test_open_project_indexes_under_canonical_identity(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "main.py").write_text(
            "def main():\n    pass",
            encoding="utf-8",
        )

        store = FakeVectorStore()

        initialization = ProjectInitializationService(
            project_service=ProjectService(
                repository=ProjectRepository(),
            ),
            repository_service=RepositoryService(
                scanner=RepositoryScanner(),
                metadata_extractor=RepositoryMetadataExtractor(),
            ),
            indexing_service=make_indexing_service(
                store,
            ),
        )

        project, _ = initialization.open_project(
            non_canonical_spelling(
                tmp_path,
            ),
        )

        canonical = str(
            tmp_path.resolve(),
        )

        assert str(project.root_directory) == canonical

        assert store.get_chunk_ids(
            where={
                "root_directory": canonical,
            },
        ) == list(
            store._chunks.keys(),
        )


class TestCorrectReIndexing:
    """Re-indexing must keep the stored index in sync with disk."""

    def test_reindex_unchanged_repository_is_idempotent(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "main.py").write_text(
            "def main():\n    print('hello')",
            encoding="utf-8",
        )

        store = FakeVectorStore()

        service = make_indexing_service(
            store,
        )

        first = service.index_repository(
            tmp_path,
        )

        first_ids = set(
            store._chunks.keys(),
        )

        second = service.index_repository(
            tmp_path,
        )

        assert second.indexed_chunks == first.indexed_chunks

        assert set(store._chunks.keys()) == first_ids

    def test_reindex_modified_file_replaces_old_chunks(
        self,
        tmp_path: Path,
    ) -> None:
        main_py = tmp_path / "main.py"

        main_py.write_text(
            "def main():\n    print('hello')",
            encoding="utf-8",
        )

        (tmp_path / "utils.py").write_text(
            "def add(a, b):\n    return a + b",
            encoding="utf-8",
        )

        store = FakeVectorStore()

        service = make_indexing_service(
            store,
        )

        service.index_repository(
            tmp_path,
        )

        old_main_ids = store.chunk_ids_by_file(
            "main.py",
        )

        main_py.write_text(
            "def main():\n    print('hello world')",
            encoding="utf-8",
        )

        service.index_repository(
            tmp_path,
        )

        new_main_ids = store.chunk_ids_by_file(
            "main.py",
        )

        assert old_main_ids

        assert new_main_ids

        assert not (old_main_ids & new_main_ids)

        assert old_main_ids.isdisjoint(
            store._chunks.keys(),
        )

        assert store.chunk_ids_by_file(
            "utils.py",
        )

    def test_reindex_deleted_file_removes_chunks(
        self,
        tmp_path: Path,
    ) -> None:
        keep_py = tmp_path / "keep.py"

        keep_py.write_text(
            "def keep():\n    pass",
            encoding="utf-8",
        )

        removed_py = tmp_path / "removed.py"

        removed_py.write_text(
            "def removed():\n    pass",
            encoding="utf-8",
        )

        store = FakeVectorStore()

        service = make_indexing_service(
            store,
        )

        service.index_repository(
            tmp_path,
        )

        keep_ids = store.chunk_ids_by_file(
            "keep.py",
        )

        removed_ids = store.chunk_ids_by_file(
            "removed.py",
        )

        assert keep_ids

        assert removed_ids

        removed_py.unlink()

        service.index_repository(
            tmp_path,
        )

        assert removed_ids.isdisjoint(
            store._chunks.keys(),
        )

        assert (
            store.chunk_ids_by_file(
                "keep.py",
            )
            == keep_ids
        )

    def test_repeated_reindexing_does_not_accumulate(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "main.py").write_text(
            "x = 1",
            encoding="utf-8",
        )

        store = FakeVectorStore()

        service = make_indexing_service(
            store,
        )

        for _ in range(3):
            service.index_repository(
                tmp_path,
            )

        assert len(store._chunks) == len(
            store.get_chunk_ids(
                where={
                    "root_directory": str(
                        tmp_path.resolve(),
                    ),
                },
            ),
        )


class TestProjectSwitching:
    """Repository scopes must stay isolated across switches."""

    def test_switching_repositories_keeps_scopes_isolated(
        self,
        tmp_path: Path,
    ) -> None:
        repo_a = tmp_path / "repo_a"

        repo_a.mkdir()

        repo_b = tmp_path / "repo_b"

        repo_b.mkdir()

        (repo_a / "alpha.py").write_text(
            "def alpha():\n    return 'a'",
            encoding="utf-8",
        )

        (repo_b / "beta.py").write_text(
            "def beta():\n    return 'b'",
            encoding="utf-8",
        )

        store = FakeVectorStore()

        service = make_indexing_service(
            store,
        )

        service.index_repository(
            repo_a,
        )

        alpha_ids = store.chunk_ids_by_file(
            "alpha.py",
        )

        service.index_repository(
            repo_b,
        )

        beta_ids = store.chunk_ids_by_file(
            "beta.py",
        )

        service.index_repository(
            repo_a,
        )

        scope_a = store.get_chunk_ids(
            where={
                "root_directory": str(
                    repo_a.resolve(),
                ),
            },
        )

        scope_b = store.get_chunk_ids(
            where={
                "root_directory": str(
                    repo_b.resolve(),
                ),
            },
        )

        assert set(scope_a) == alpha_ids

        assert set(scope_b) == beta_ids

        assert not (set(scope_a) & set(scope_b))

        assert alpha_ids.issubset(
            store._chunks.keys(),
        )

        assert beta_ids.issubset(
            store._chunks.keys(),
        )


class TestStaleRemovalUnit:
    """Stale chunk removal on the indexer."""

    def test_remove_stale_chunks_deletes_only_stale(
        self,
    ) -> None:
        store = FakeVectorStore()

        store.add(
            [
                self._make_chunk("c1"),
                self._make_chunk("c2"),
                self._make_chunk("c3"),
            ],
        )

        indexer = RepositoryIndexer(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store_resolver=StaticVectorStoreResolver(
                store,
            ),
        )

        removed = indexer.remove_stale_chunks(
            root_directory="/projects/alpha",
            keep_chunk_ids=["c1"],
        )

        assert removed == 2

        assert set(store._chunks.keys()) == {
            "c1",
        }

    def test_remove_stale_chunks_keeps_all_when_ids_match(
        self,
    ) -> None:
        store = FakeVectorStore()

        store.add(
            [
                self._make_chunk("c1"),
            ],
        )

        indexer = RepositoryIndexer(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store_resolver=StaticVectorStoreResolver(
                store,
            ),
        )

        removed = indexer.remove_stale_chunks(
            root_directory="/projects/alpha",
            keep_chunk_ids=["c1"],
        )

        assert removed == 0

        assert set(store._chunks.keys()) == {
            "c1",
        }

    @staticmethod
    def _make_chunk(
        chunk_id: str,
    ) -> IndexedChunk:
        """Create a chunk scoped to a fixed repository."""

        return IndexedChunk(
            chunk_id=chunk_id,
            content=f"content {chunk_id}",
            metadata=RepositoryChunkMetadata(
                relative_path=Path(
                    f"{chunk_id}.py",
                ),
                language="Python",
                mime_type="text/x-python",
                sha256="abc",
                root_directory="/projects/alpha",
            ),
            boundary=ChunkBoundary(
                start_line=1,
                end_line=1,
            ),
            embedding=EmbeddingVector(
                values=[1.0],
            ),
        )
