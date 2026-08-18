# Guide: Adding a Vector Store

> **Status:** Complete
> **Last Updated:** Sprint 13

---

## Objective

Implement a new vector store backend for semantic search (e.g., PostgreSQL+pgvector, FAISS, Qdrant) while preserving the `VectorStore` interface.

## Steps

### 1. Implement the Interface

```python
from collections.abc import Sequence

from app.indexing.models import EmbeddingVector, IndexedChunk
from app.indexing.retrieval_models import SearchHit
from app.indexing.stores import VectorStore


class MyVectorStore(VectorStore):
    """MyStore adapter."""

    def add(self, chunks: Sequence[IndexedChunk]) -> None:
        """Store indexed chunks."""

    def search(
        self,
        query_embedding: EmbeddingVector,
        limit: int = 10,
        where: dict | None = None,
    ) -> list[SearchHit]:
        """Return the most similar indexed chunks."""

    def get_chunk_ids(self, where: dict | None = None) -> list[str]:
        """Return chunk ids matching the filter."""

    def delete(self, chunk_ids: Sequence[str]) -> None:
        """Delete indexed chunks."""

    def clear(self) -> None:
        """Remove all indexed chunks."""
```

### 2. Add a Resolver

Subsystems depend on the `VectorStoreResolver` protocol (`app/indexing/store_resolver.py`), never on a concrete store. Add a resolver that returns the new store for a project root:

```python
class ProjectMyStoreResolver:
    """Resolve the project-scoped MyStore for a project root."""

    def for_project(
        self,
        root_directory: str,
        *,
        create: bool = False,
    ) -> VectorStore | None:
        """Return the store for a project, or None when unavailable."""
```

### 3. Register the Resolver

In `app/dependencies/providers.py`, extend `get_vector_store_resolver()` to return a resolver producing the new store. Indexing and retrieval require no changes — they depend on the resolver and the `VectorStore` interface, not on ChromaDB.

### 4. Clear and Re-Index

Changing vector stores invalidates existing embeddings. Clear the old store and re-index:

```bash
# Delete existing vector data
# Re-open project to trigger indexing
```

### 5. Verify

- Indexing produces results in the new store
- Retrieval returns results from the new store (per opened project, never cross-project)
- All existing tests pass

## Related

- [Indexing Architecture](../../architecture/backend/indexing.md)
- [Retrieval Architecture](../../architecture/backend/retrieval.md)
- [Storage Architecture](../../architecture/backend/storage.md)
- ADR-0006: ChromaVectorStore
