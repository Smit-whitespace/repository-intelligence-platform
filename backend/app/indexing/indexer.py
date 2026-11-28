"""Repository indexing service."""

import logging
from collections.abc import Collection, Sequence

from app.indexing.exceptions import EmbeddingError, EmbeddingModelChangedError
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
    IndexingResult,
    IndexStatus,
)
from app.indexing.providers import EmbeddingProvider
from app.indexing.store_resolver import VectorStoreResolver
from app.indexing.stores import (
    EMBEDDING_DIMENSION_METADATA_KEY,
    EMBEDDING_MODEL_METADATA_KEY,
    VectorStore,
)
from app.repository.models import RepositoryChunk

logger = logging.getLogger(__name__)


class RepositoryIndexer:
    """Indexes repository chunks.

    The destination vector store is resolved from the chunk metadata's
    project ``root_directory`` so each project's chunks are written to
    that project's own persistent store — never to a store chosen by
    the process working directory.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store_resolver: VectorStoreResolver,
    ) -> None:
        """Initialize the repository indexer."""

        self._embedding_provider = embedding_provider

        self._vector_store_resolver = vector_store_resolver

        self._pending_rebuilds: dict[str, str] = {}
        """Project roots whose index must be cleared before the next write,
        mapped to the model that built the old index (for logging)."""

    @property
    def configured_embedding_model(
        self,
    ) -> str:
        """Identity of the embedding model the configuration selects now."""

        return self._embedding_provider.identity

    def status(
        self,
        root_directory: str,
    ) -> IndexStatus:
        """Report whether a project is indexed, and with which model."""

        configured = self._embedding_provider.identity

        vector_store = self._vector_store_resolver.for_project(
            root_directory=root_directory,
        )

        if vector_store is None:
            return IndexStatus(
                indexed=False,
                configured_embedding_model=configured,
                compatible=False,
            )

        metadata = vector_store.get_index_metadata() or {}

        built_with = metadata.get(
            EMBEDDING_MODEL_METADATA_KEY,
        )

        return IndexStatus(
            indexed=True,
            embedding_model=(
                str(built_with)
                if built_with is not None
                else None
            ),
            configured_embedding_model=configured,
            compatible=built_with is None or built_with == configured,
        )

    def existing_chunk_ids_by_path(
        self,
        root_directory: str,
    ) -> dict[str, set[str]]:
        """Existing chunk ids grouped by file (empty if unknown or rebuilding)."""

        if root_directory in self._pending_rebuilds:
            return {}

        vector_store = self._vector_store_resolver.for_project(
            root_directory=root_directory,
        )

        if vector_store is None:
            return {}

        return vector_store.get_chunk_ids_by_path(
            where={
                "root_directory": root_directory,
            },
        ) or {}

    def indexed_file_hashes(
        self,
        root_directory: str,
    ) -> dict[str, str]:
        """Stored SHA-256 per indexed file (empty if unknown or rebuilding)."""

        if root_directory in self._pending_rebuilds:
            return {}

        vector_store = self._vector_store_resolver.for_project(
            root_directory=root_directory,
        )

        if vector_store is None:
            return {}

        return vector_store.get_file_hashes(
            where={
                "root_directory": root_directory,
            },
        ) or {}

    def existing_chunk_ids(
        self,
        root_directory: str,
    ) -> set[str]:
        """Return the ids of chunks already indexed for a project.

        Empty when the project has no index yet, or when this run will
        rebuild it (``prepare`` found a different embedding model), so
        everything is embedded again with the configured model.
        """

        if root_directory in self._pending_rebuilds:
            return set()

        vector_store = self._vector_store_resolver.for_project(
            root_directory=root_directory,
        )

        if vector_store is None:
            return set()

        return set(
            vector_store.get_chunk_ids(
                where={
                    "root_directory": root_directory,
                },
            ),
        )

    def prepare(
        self,
        root_directory: str,
    ) -> None:
        """Decide whether this indexing run must rebuild the index.

        If the index was built by a different embedding model, or before
        the model was recorded (so it cannot be verified), this run
        rebuilds it. Its vectors would otherwise mix with incomparable
        ones, and because chunk ids do not include the model, unchanged
        chunks would keep their old vectors forever.

        The clear itself is deferred until the first batch has been
        embedded successfully (see ``index``). If the embedding provider
        is down or the new model is missing, the old index survives
        intact instead of being destroyed for nothing.

        Only an explicit indexing run calls this; changing the configured
        model never triggers a reindex by itself.
        """

        self._pending_rebuilds.pop(
            root_directory,
            None,
        )

        vector_store = self._vector_store_resolver.for_project(
            root_directory=root_directory,
        )

        if vector_store is None:
            return

        metadata = vector_store.get_index_metadata()

        if metadata is None:
            return

        built_with = metadata.get(
            EMBEDDING_MODEL_METADATA_KEY,
        )

        if built_with == self._embedding_provider.identity:
            return

        self._pending_rebuilds[root_directory] = str(
            built_with or "an unrecorded embedding model",
        )

    def index(
        self,
        chunks: Sequence[RepositoryChunk],
        expected_model: str | None = None,
    ) -> IndexingResult:
        """Index repository chunks.

        With ``expected_model``, the chunks are written only if that is
        still the configured model after embedding, and the index is
        stamped with it; otherwise ``EmbeddingModelChangedError`` is
        raised and nothing is written.
        """

        if not chunks:
            return IndexingResult(
                scanned_files=0,
                indexed_files=0,
                indexed_chunks=0,
                skipped_files=0,
                failed_files=0,
            )

        root_directory = chunks[
            0
        ].metadata.root_directory

        if not root_directory:
            raise ValueError(
                "Chunks must carry a project root_directory before indexing."
            )

        vector_store = self._vector_store_resolver.for_project(
            root_directory=root_directory,
            create=True,
        )

        if vector_store is None:
            raise RuntimeError(
                f"Unable to resolve vector store for project: "
                f"{root_directory}"
            )

        texts = [chunk.content for chunk in chunks]

        # Read before embedding: the stamp names the model asked to embed.
        identity = self._embedding_provider.identity

        self._check_model(
            expected_model,
            identity,
        )

        embeddings = self._embedding_provider.embed(
            texts,
        )

        if len(embeddings) != len(chunks):
            raise EmbeddingError(
                "Embedding provider returned an unexpected number of embedding vectors."
            )

        # The configuration may have changed while embedding; the lazy
        # provider would then have embedded with the new model.
        self._check_model(
            expected_model,
            self._embedding_provider.identity,
        )

        indexed_chunks = [
            IndexedChunk(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                metadata=chunk.metadata,
                boundary=chunk.boundary,
                embedding=EmbeddingVector(
                    values=embedding.values,
                ),
            )
            for chunk, embedding in zip(
                chunks,
                embeddings,
            )
        ]

        old_model = self._pending_rebuilds.pop(
            root_directory,
            None,
        )

        if old_model is not None:
            logger.warning(
                "Rebuilding index for %s: built with %s, configured model is %s",
                root_directory,
                old_model,
                self._embedding_provider.identity,
            )

            vector_store.clear()

        vector_store.add(
            indexed_chunks,
        )

        self._record_embedding_model(
            vector_store=vector_store,
            identity=identity,
            dimension=len(
                embeddings[0].values,
            ),
        )

        return IndexingResult(
            scanned_files=0,
            indexed_files=0,
            indexed_chunks=len(indexed_chunks),
            skipped_files=0,
            failed_files=0,
        )

    @staticmethod
    def _check_model(
        expected_model: str | None,
        identity: str,
    ) -> None:
        if expected_model is not None and identity != expected_model:
            raise EmbeddingModelChangedError(
                f"The embedding model changed from {expected_model} to "
                f"{identity} during the update.",
            )

    def _record_embedding_model(
        self,
        vector_store: VectorStore,
        identity: str,
        dimension: int,
    ) -> None:
        """Stamp the index with the embedding model that wrote it."""

        metadata = vector_store.get_index_metadata()

        if metadata is None:
            return

        if metadata.get(EMBEDDING_MODEL_METADATA_KEY) == identity:
            return

        vector_store.set_index_metadata(
            {
                EMBEDDING_MODEL_METADATA_KEY: identity,
                EMBEDDING_DIMENSION_METADATA_KEY: dimension,
            },
        )

    def remove_stale_chunks(
        self,
        root_directory: str,
        keep_chunk_ids: Sequence[str],
    ) -> int:
        """Delete persisted chunks for the scope not re-indexed this run.

        Chunks for modified or deleted files no longer appear in
        ``keep_chunk_ids``; deleting them keeps the stored index in sync
        with the repository on disk.
        """

        if not root_directory:
            return 0

        vector_store = self._vector_store_resolver.for_project(
            root_directory=root_directory,
            create=True,
        )

        if vector_store is None:
            return 0

        existing_chunk_ids = vector_store.get_chunk_ids(
            where={
                "root_directory": root_directory,
            },
        )

        keep = set(
            keep_chunk_ids,
        )

        stale_chunk_ids = [
            chunk_id
            for chunk_id in existing_chunk_ids
            if chunk_id not in keep
        ]

        if stale_chunk_ids:
            vector_store.delete(
                stale_chunk_ids,
            )

        return len(
            stale_chunk_ids,
        )

    def remove_paths(
        self,
        root_directory: str,
        relative_paths: Sequence[str],
    ) -> int:
        """Delete every chunk of the given files; return how many."""

        if not relative_paths:
            return 0

        return self._delete_chunks_where(
            root_directory=root_directory,
            relative_path_filter={
                "$in": list(relative_paths),
            },
            keep_chunk_ids=(),
        )

    def remove_chunks_of_path_except(
        self,
        root_directory: str,
        relative_path: str,
        keep_chunk_ids: Collection[str],
    ) -> int:
        """Delete one file's chunks that are not in ``keep_chunk_ids``."""

        return self._delete_chunks_where(
            root_directory=root_directory,
            relative_path_filter=relative_path,
            keep_chunk_ids=keep_chunk_ids,
        )

    def _delete_chunks_where(
        self,
        root_directory: str,
        relative_path_filter: str | dict[str, list[str]],
        keep_chunk_ids: Collection[str],
    ) -> int:
        """Delete the project's chunks matching a path filter, except kept ids."""

        if not root_directory:
            return 0

        vector_store = self._vector_store_resolver.for_project(
            root_directory=root_directory,
        )

        if vector_store is None:
            return 0

        by_path = vector_store.get_chunk_ids_by_path(
            where={
                "$and": [
                    {
                        "root_directory": root_directory,
                    },
                    {
                        "relative_path": relative_path_filter,
                    },
                ],
            },
        ) or {}

        stale_chunk_ids = [
            chunk_id
            for chunk_ids in by_path.values()
            for chunk_id in chunk_ids
            if chunk_id not in keep_chunk_ids
        ]

        if stale_chunk_ids:
            vector_store.delete(
                stale_chunk_ids,
            )

        return len(
            stale_chunk_ids,
        )
