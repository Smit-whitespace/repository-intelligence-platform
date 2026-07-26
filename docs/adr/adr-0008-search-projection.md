# ADR-0008: Search Projection

**Status:** Adopted

**Context:**

Vector search returns raw matches from the database. These raw results (`SearchHit`) contain internal representations (vector scores, database IDs) that should not be part of the public API. Downstream consumers need a stable projection independent of the vector store internals.

**Decision:**

Retrieval maps `SearchHit` (raw vector store result) to `SearchResult` (public API projection). `SearchHit` includes `vector_score`; `SearchResult` includes `similarity_score`. The mapping transforms internal representations into API-stable models.

**Consequences:**

Positive:
- API consumers are isolated from vector store internals
- Changes to vector store models don't affect API responses
- `SearchResult` is a stable contract

Negative:
- Additional mapping layer in retrieval pipeline
- Two similar model classes must be maintained

**Alternatives Considered:**

- Expose `SearchHit` directly: rejected — couples API to vector store internals
- Single search model: rejected — conflates internal and external representations
