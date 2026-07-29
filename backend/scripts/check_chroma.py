"""Manual ChromaDB connectivity test."""

from pathlib import Path

from app.core.config.provider import (
    get_settings,
)
from app.indexing.chroma_store import (
    ChromaVectorStore,
)
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.repository.models import (
    ChunkBoundary,
    RepositoryChunkMetadata,
)


def main() -> None:
    """Run manual ChromaDB test."""

    settings = get_settings()

    store = ChromaVectorStore(
        settings.chroma,
    )

    print("Clearing collection...")

    store.clear()

    chunk = IndexedChunk(
        chunk_id="demo",
        content="Hello RIP",
        embedding=EmbeddingVector(
            values=[0.1, 0.2, 0.3],
        ),
        metadata=RepositoryChunkMetadata(
            relative_path=Path(
                "demo.py",
            ),
            language="Python",
            mime_type="text/x-python",
            sha256="demo",
        ),
        boundary=ChunkBoundary(
            start_line=1,
            end_line=1,
        ),
    )

    print("Adding chunk...")

    store.add(
        [
            chunk,
        ]
    )

    print("Deleting chunk...")

    store.delete(
        [
            "demo",
        ]
    )

    print("ChromaDB verification successful.")


if __name__ == "__main__":
    main()
