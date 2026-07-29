"""ChromaDB vector store."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import chromadb
from chromadb import Collection
from chromadb.api import ClientAPI

from app.core.config.models import ChromaSettings
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.indexing.retrieval_models import SearchHit
from app.indexing.stores import VectorStore
from app.repository.models import (
    ChunkBoundary,
    ChunkType,
    RepositoryChunkMetadata,
)


class ChromaVectorStore(VectorStore):
    """Persistent ChromaDB-backed vector store."""

    def __init__(
        self,
        settings: ChromaSettings,
    ) -> None:
        """Initialize the ChromaDB client."""

        self._client: ClientAPI = chromadb.PersistentClient(
            path=str(
                settings.persist_directory,
            ),
        )

        self._collection: Collection = self._client.get_or_create_collection(
            name=settings.collection_name,
        )

    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """Store indexed chunks."""

        if not chunks:
            return

        self._collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=cast(
                list[Sequence[float]],
                [chunk.embedding.values for chunk in chunks],
            ),
            metadatas=[
                {
                    **chunk.metadata.model_dump(
                        mode="json",
                    ),
                    **chunk.boundary.model_dump(
                        mode="json",
                    ),
                }
                for chunk in chunks
            ],
        )

    def search(
        self,
        query_embedding: EmbeddingVector,
        limit: int = 10,
        where: dict | None = None,
    ) -> list[SearchHit]:
        """Return the most similar indexed chunks."""

        import logging
        logging.warning("[INSTRUMENT] ChromaVectorStore.search() — collection=%r, limit=%s, where=%s", self._collection.name, limit, where)

        raw_result = cast(
            dict[str, Any],
            self._collection.query(
                query_embeddings=cast(
                    list[Sequence[float]],
                    [
                        query_embedding.values,
                    ],
                ),
                n_results=limit,
                where=where,
            ),
        )

        ids = cast(
            list[list[str]],
            raw_result.get(
                "ids",
                [],
            ),
        )

        documents = cast(
            list[list[str]],
            raw_result.get(
                "documents",
                [],
            ),
        )

        metadatas = cast(
            list[list[dict[str, Any] | None]],
            raw_result.get(
                "metadatas",
                [],
            ),
        )

        distances = cast(
            list[list[float]],
            raw_result.get(
                "distances",
                [],
            ),
        )

        if not ids or not documents or not metadatas or not distances:
            logging.warning("[INSTRUMENT] Chroma query returned empty (no matching chunks)")
            return []

        batch_ids = ids[0]
        batch_documents = documents[0]
        batch_metadatas = metadatas[0]
        batch_distances = distances[0]

        result_count = len(
            batch_ids,
        )

        if not (
            result_count
            == len(batch_documents)
            == len(batch_metadatas)
            == len(batch_distances)
        ):
            raise RuntimeError(
                "Inconsistent Chroma query result.",
            )

        if result_count == 0:
            return []

        return [
            self._create_search_hit(
                chunk_id=chunk_id,
                content=content,
                metadata=metadata,
                distance=distance,
            )
            for (
                chunk_id,
                content,
                metadata,
                distance,
            ) in zip(
                batch_ids,
                batch_documents,
                batch_metadatas,
                batch_distances,
                strict=True,
            )
        ]

    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        """Delete indexed chunks."""

        if not chunk_ids:
            return

        self._collection.delete(
            ids=list(
                chunk_ids,
            ),
        )

    def clear(
        self,
    ) -> None:
        """Remove all indexed chunks."""

        self._client.delete_collection(
            self._collection.name,
        )

        self._collection = self._client.get_or_create_collection(
            name=self._collection.name,
        )

    def _create_search_hit(
        self,
        chunk_id: str,
        content: str,
        metadata: dict[str, Any] | None,
        distance: float,
    ) -> SearchHit:
        """Build a search hit from persisted Chroma data."""

        if metadata is None:
            raise RuntimeError(
                "Missing metadata in Chroma query result.",
            )

        return SearchHit(
            chunk_id=chunk_id,
            content=content,
            metadata=self._build_repository_metadata(
                metadata,
            ),
            boundary=self._build_chunk_boundary(
                metadata,
            ),
            vector_score=distance,
        )

    def _build_repository_metadata(
        self,
        metadata: dict[str, Any],
    ) -> RepositoryChunkMetadata:
        """Reconstruct repository metadata."""

        return RepositoryChunkMetadata(
            relative_path=Path(
                cast(
                    str,
                    metadata["relative_path"],
                ),
            ),
            language=cast(
                str | None,
                metadata["language"],
            ),
            mime_type=cast(
                str | None,
                metadata["mime_type"],
            ),
            sha256=cast(
                str,
                metadata["sha256"],
            ),
        )

    def _build_chunk_boundary(
        self,
        metadata: dict[str, Any],
    ) -> ChunkBoundary:
        """Reconstruct chunk boundary information."""

        return ChunkBoundary(
            start_line=cast(
                int,
                metadata["start_line"],
            ),
            end_line=cast(
                int,
                metadata["end_line"],
            ),
            chunk_type=ChunkType(
                cast(
                    str,
                    metadata["chunk_type"],
                ),
            ),
        )
