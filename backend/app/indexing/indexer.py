"""Repository indexing service."""

from collections.abc import Sequence

from app.indexing.exceptions import EmbeddingError
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
    IndexingResult,
)
from app.indexing.providers import EmbeddingProvider
from app.indexing.stores import VectorStore
from app.repository.models import RepositoryChunk


class RepositoryIndexer:
    """Indexes repository chunks."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        """Initialize the repository indexer."""

        self._embedding_provider = embedding_provider

        self._vector_store = vector_store

    def index(
        self,
        chunks: Sequence[RepositoryChunk],
    ) -> IndexingResult:
        """Index repository chunks."""

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

        self._vector_store.add(
            indexed_chunks,
        )

        return IndexingResult(
            scanned_files=0,
            indexed_files=0,
            indexed_chunks=len(indexed_chunks),
            skipped_files=0,
            failed_files=0,
        )
