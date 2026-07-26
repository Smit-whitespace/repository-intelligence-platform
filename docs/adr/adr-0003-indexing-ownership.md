# ADR-0003: Indexing Ownership

**Status:** Adopted

**Context:**

Repository chunks must be converted into searchable semantic representations. Embedding generation and vector storage are new concerns that do not belong in the Repository subsystem. Clear ownership prevents architectural coupling between repository structure and semantic representation.

**Decision:**

The Indexing subsystem owns all embedding generation and vector persistence coordination. It consumes `RepositoryChunk` from the Repository subsystem and produces `IndexedChunk`. Embedding and vector store are abstract interfaces.

**Consequences:**

Positive:
- Repository subsystem is not coupled to any embedding strategy
- Embedding provider and vector store can be swapped independently
- Indexing is testable in isolation with mock providers

Negative:
- Indexing must coordinate two external services (embedding + vector store)
- `IndexingResult` is the only output — detailed error reporting is limited

**Alternatives Considered:**

- Embedding in Repository subsystem: rejected — couples repository logic to AI infrastructure
- Single combined Indexing+Retrieval subsystem: rejected — creates circular dependency risk
