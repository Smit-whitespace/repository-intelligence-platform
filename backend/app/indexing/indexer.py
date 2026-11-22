"""Repository indexing service."""

import logging
from collections.abc import Sequence

from app.indexing.exceptions import EmbeddingError
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
    IndexingResult,
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

    def prepare(
        self,
        root_directory: str,
    ) -> None:
        """Make a project's index safe to write with the current model.

        If the index was built by a different embedding model, or before
        the model was recorded (so it cannot be verified), it is cleared
        and rebuilt by this indexing run. Its vectors would otherwise mix
        with incomparable ones, and because chunk ids do not include the
        model, unchanged chunks would keep their old vectors forever.

        Indexing re-embeds every chunk anyway, so clearing first costs
        nothing extra. Only an explicit indexing run calls this; changing
        the configured model never triggers a reindex by itself.
        """

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

        logger.warning(
            "Rebuilding index for %s: built with %s, configured model is %s",
            root_directory,
            built_with or "an unrecorded embedding model",
            self._embedding_provider.identity,
        )

        vector_store.clear()

    def index(
        self,
        chunks: Sequence[RepositoryChunk],
    ) -> IndexingResult:
        """Index repository chunks."""

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

        embeddings = self._embedding_provider.embed(
            texts,
        )

        if len(embeddings) != len(chunks):
            raise EmbeddingError(
                "Embedding provider returned an unexpected number of embedding vectors."
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

        vector_store.add(
            indexed_chunks,
        )

        self._record_embedding_model(
            vector_store=vector_store,
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

    def _record_embedding_model(
        self,
        vector_store: VectorStore,
        dimension: int,
    ) -> None:
        """Stamp the index with the embedding model that wrote it."""

        metadata = vector_store.get_index_metadata()

        if metadata is None:
            return

        identity = self._embedding_provider.identity

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
