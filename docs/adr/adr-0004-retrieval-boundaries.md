# ADR-0004: Retrieval Boundaries

**Status:** Adopted

**Context:**

Semantic search over indexed content is required for repository-aware chat. If retrieval is coupled to indexing, changes in embedding strategy would require changes in search logic. If coupled to chat, chat would need to understand vector search internals.

**Decision:**

Retrieval is a separate subsystem. It depends on `EmbeddingProvider` and `VectorStore` but never performs indexing. It returns `SearchResponse` containing `SearchResult` projections — not raw `IndexedChunk` objects. `ChatService` consumes retrieval but never indexes.

**Consequences:**

Positive:
- Retrieval can evolve independently of indexing
- Retrieval can be tested without an indexing pipeline
- Chat remains decoupled from vector search internals

Negative:
- Duplicated embedding provider dependency (both indexing and retrieval embed)
- Additional abstraction layer between chat and vector store

**Alternatives Considered:**

- Retrieval as part of Indexing: rejected — creates circular dependency with chat
- Retrieval as part of Chat: rejected — couples chat to vector search implementation
