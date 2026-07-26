# Guide: Adding a Vector Store

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Objective

Implement a new vector store backend for semantic search (e.g., PostgreSQL+pgvector, FAISS, Qdrant) while preserving the `VectorStore` interface.

## Steps

### 1. Implement the Interface

```python
from app.indexing.stores import VectorStore
from app.indexing.models import EmbeddingVector
from app.indexing.retrieval_models import SearchHit
from app.repository.models import RepositoryChunk


class MyVectorStore(VectorStore):
    """MyStore adapter."""

    def __init__(self, ...) -> None:
        """Initialize connection."""

    def index(
        self,
        chunks: Sequence[RepositoryChunk],
        embeddings: Sequence[EmbeddingVector],
    ) -> IndexingResult:
        """Store chunks with their embeddings."""
        # Implementation specific to MyStore

    def find_similar(
        self,
        embedding: EmbeddingVector,
        limit: int,
    ) -> list[SearchHit]:
        """Search for similar vectors."""
        # Implementation specific to MyStore
```

### 2. Add Provider

In `app/dependencies/providers.py`:

```python
@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    """Return the vector store."""

    return MyVectorStore(
        # configuration
    )
```

### 3. Update the Existing Provider

Replace the ChromaVectorStore provider. The indexing and retrieval subsystems require no changes — they depend on the `VectorStore` interface, not on ChromaDB.

### 4. Clear and Re-Index

Changing vector stores invalidates existing embeddings. Clear the old store and re-index:

```bash
# Delete existing vector data
# Re-open project to trigger indexing
```

### 5. Verify

- Indexing produces results in the new store
- Retrieval returns results from the new store
- All existing tests pass

## Related

- [Indexing Architecture](../../architecture/backend/indexing.md)
- [Retrieval Architecture](../../architecture/backend/retrieval.md)
- [Storage Architecture](../../architecture/backend/storage.md)
- ADR-0006: ChromaVectorStore
