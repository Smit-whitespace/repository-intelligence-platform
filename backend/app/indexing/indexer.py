"""Repository indexing service."""

from collections.abc import Sequence

from app.indexing.exceptions import EmbeddingError
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
    IndexingResult,
)
from app.indexing.providers import EmbeddingProvider
from app.indexing.store_resolver import VectorStoreResolver
from app.repository.models import RepositoryChunk


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

        return IndexingResult(
            scanned_files=0,
            indexed_files=0,
            indexed_chunks=len(indexed_chunks),
            skipped_files=0,
            failed_files=0,
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
