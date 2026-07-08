"""Tests for ChromaDB vector store."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from app.core.config.models import ChromaSettings
from app.indexing.chroma_store import ChromaVectorStore
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.repository.models import (
    ChunkBoundary,
    ChunkType,
    RepositoryChunkMetadata,
)


def create_chunk() -> IndexedChunk:
    """Create a sample indexed chunk."""

    return IndexedChunk(
        chunk_id="chunk-1",
        content="def main():\n    pass",
        metadata=RepositoryChunkMetadata(
            relative_path=Path(
                "main.py",
            ),
            language="python",
            mime_type="text/x-python",
            sha256="abc123",
        ),
        boundary=ChunkBoundary(
            start_line=1,
            end_line=2,
            chunk_type=ChunkType.FUNCTION,
        ),
        embedding=EmbeddingVector(
            values=[
                1.0,
                2.0,
                3.0,
            ],
        ),
    )


def create_store() -> tuple[
    ChromaVectorStore,
    MagicMock,
    MagicMock,
]:
    """Create a vector store with mocked ChromaDB."""

    settings = ChromaSettings()

    with patch(
        "app.indexing.chroma_store.chromadb.PersistentClient",
    ) as mock_client_class:
        client = MagicMock()

        collection = MagicMock()

        collection.name = (
            settings.collection_name
        )

        client.get_or_create_collection.return_value = (
            collection
        )

        mock_client_class.return_value = (
            client
        )

        store = ChromaVectorStore(
            settings,
        )

    return (
        store,
        client,
        collection,
    )


def test_add_stores_indexed_chunks() -> None:
    """Store indexed chunks."""

    (
        store,
        _client,
        collection,
    ) = create_store()

    chunk = create_chunk()

    store.add(
        [
            chunk,
        ],
    )

    collection.add.assert_called_once_with(
        ids=[
            "chunk-1",
        ],
        documents=[
            "def main():\n    pass",
        ],
        embeddings=[
            [
                1.0,
                2.0,
                3.0,
            ],
        ],
        metadatas=[
            {
                "relative_path": "main.py",
                "language": "python",
                "mime_type": "text/x-python",
                "sha256": "abc123",
                "start_line": 1,
                "end_line": 2,
                "chunk_type": "function",
            },
        ],
    )


def test_add_empty_chunks_is_no_op() -> None:
    """Empty chunk list should not be persisted."""

    (
        store,
        _client,
        collection,
    ) = create_store()

    store.add(
        [],
    )

    collection.add.assert_not_called()


def test_search_returns_search_hits() -> None:
    """Search should reconstruct search hits."""

    (
        store,
        _client,
        collection,
    ) = create_store()

    collection.query.return_value = {
        "ids": [
            [
                "chunk-1",
            ],
        ],
        "documents": [
            [
                "def main():\n    pass",
            ],
        ],
        "metadatas": [
            [
                {
                    "relative_path": "main.py",
                    "language": "python",
                    "mime_type": "text/x-python",
                    "sha256": "abc123",
                    "start_line": 1,
                    "end_line": 2,
                    "chunk_type": "function",
                },
            ],
        ],
        "distances": [
            [
                0.123,
            ],
        ],
    }

    embedding = EmbeddingVector(
        values=[
            1.0,
            2.0,
            3.0,
        ],
    )

    results = store.search(
        embedding,
        limit=5,
    )

    collection.query.assert_called_once_with(
        query_embeddings=[
            [
                1.0,
                2.0,
                3.0,
            ],
        ],
        n_results=5,
    )

    assert len(
        results,
    ) == 1

    hit = results[0]

    assert hit.chunk_id == "chunk-1"

    assert (
        hit.content
        == "def main():\n    pass"
    )

    assert (
        hit.metadata.relative_path
        == Path("main.py")
    )

    assert (
        hit.metadata.language
        == "python"
    )

    assert (
        hit.metadata.mime_type
        == "text/x-python"
    )

    assert (
        hit.metadata.sha256
        == "abc123"
    )

    assert (
        hit.boundary.start_line
        == 1
    )

    assert (
        hit.boundary.end_line
        == 2
    )

    assert (
        hit.boundary.chunk_type
        == ChunkType.FUNCTION
    )

    assert (
        hit.vector_score
        == 0.123
    )
def test_search_returns_empty_list_for_empty_response() -> None:
    """Empty Chroma response should return no search hits."""

    (
        store,
        _client,
        collection,
    ) = create_store()

    collection.query.return_value = {}

    results = store.search(
        EmbeddingVector(
            values=[
                1.0,
            ],
        ),
    )

    assert results == []


def test_search_returns_empty_list_for_empty_batch() -> None:
    """Empty query batches should return no search hits."""

    (
        store,
        _client,
        collection,
    ) = create_store()

    collection.query.return_value = {
        "ids": [
            [],
        ],
        "documents": [
            [],
        ],
        "metadatas": [
            [],
        ],
        "distances": [
            [],
        ],
    }

    results = store.search(
        EmbeddingVector(
            values=[
                1.0,
            ],
        ),
    )

    assert results == []


def test_search_raises_for_inconsistent_query_result() -> None:
    """Mismatched Chroma result lengths should raise."""

    (
        store,
        _client,
        collection,
    ) = create_store()

    collection.query.return_value = {
        "ids": [
            [
                "chunk-1",
            ],
        ],
        "documents": [
            [
                "content",
            ],
        ],
        "metadatas": [
            [
                {
                    "relative_path": "main.py",
                    "language": "python",
                    "mime_type": "text/x-python",
                    "sha256": "abc123",
                    "start_line": 1,
                    "end_line": 1,
                    "chunk_type": "function",
                },
            ],
        ],
        "distances": [
            [],
        ],
    }

    with pytest.raises(
        RuntimeError,
        match="Inconsistent Chroma query result.",
    ):
        store.search(
            EmbeddingVector(
                values=[
                    1.0,
                ],
            ),
        )


def test_search_raises_when_metadata_is_missing() -> None:
    """Missing metadata should raise."""

    (
        store,
        _client,
        collection,
    ) = create_store()

    collection.query.return_value = {
        "ids": [
            [
                "chunk-1",
            ],
        ],
        "documents": [
            [
                "content",
            ],
        ],
        "metadatas": [
            [
                None,
            ],
        ],
        "distances": [
            [
                0.1,
            ],
        ],
    }

    with pytest.raises(
        RuntimeError,
        match="Missing metadata in Chroma query result.",
    ):
        store.search(
            EmbeddingVector(
                values=[
                    1.0,
                ],
            ),
        )

def test_delete_deletes_chunk_ids() -> None:
    """Delete indexed chunks."""

    (
        store,
        _client,
        collection,
    ) = create_store()

    store.delete(
        [
            "chunk-1",
            "chunk-2",
        ],
    )

    collection.delete.assert_called_once_with(
        ids=[
            "chunk-1",
            "chunk-2",
        ],
    )


def test_delete_empty_chunk_ids_is_no_op() -> None:
    """Empty chunk identifier list should not call Chroma."""

    (
        store,
        _client,
        collection,
    ) = create_store()

    store.delete(
        [],
    )

    collection.delete.assert_not_called()


def test_clear_recreates_collection() -> None:
    """Clear should recreate the Chroma collection."""

    settings = ChromaSettings()

    with patch(
        "app.indexing.chroma_store.chromadb.PersistentClient",
    ) as mock_client_class:
        client = MagicMock()

        original_collection = MagicMock()

        original_collection.name = (
            settings.collection_name
        )

        recreated_collection = MagicMock()

        recreated_collection.name = (
            settings.collection_name
        )

        client.get_or_create_collection.side_effect = [
            original_collection,
            recreated_collection,
        ]

        mock_client_class.return_value = (
            client
        )

        store = ChromaVectorStore(
            settings,
        )

        store.clear()

        client.delete_collection.assert_called_once_with(
            settings.collection_name,
        )

        assert (
            client.get_or_create_collection.call_count
            == 2
        )

        client.get_or_create_collection.assert_called_with(
            name=settings.collection_name,
        )

        assert (
            store._collection
            is recreated_collection
        )