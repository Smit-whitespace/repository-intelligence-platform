# ADR-0006: ChromaVectorStore Ownership

**Status:** Adopted

**Context:**

Vector persistence is required for semantic search. Several vector database options exist (ChromaDB, PostgreSQL+pgvector, Pinecone, Qdrant). A decision was needed for Version 1 that balances simplicity, local execution, and adequate performance.

**Decision:**

ChromaDB is the vector store for Version 1. It is accessed through the `VectorStore` interface in `app/indexing/stores.py`. All vector CRUD and similarity search is encapsulated behind this interface.

**Consequences:**

Positive:
- ChromaDB runs embedded — no external server required
- Simple setup for local development
- Abstract interface allows future replacement

Negative:
- ChromaDB version is pinned; upgrades may require adapter changes
- Limited to single-node deployment
- Some advanced search features (filtering, hybrid search) are not exposed

**Alternatives Considered:**

- PostgreSQL + pgvector: rejected — would require PostgreSQL dependency and migration system
- Pinecone/Qdrant: rejected — require cloud services, violate offline-first
- FAISS: rejected — no built-in persistence
