# ADR-0010: Filesystem Persistence

**Status:** Adopted

**Context:**

Project metadata, snapshots, and configuration must be persisted between sessions. Several storage strategies exist: filesystem JSON, relational databases, key-value stores. The chosen strategy must be simple, require no external services, and be trivially inspectable.

**Decision:**

Filesystem-based persistence using JSON files in a `.local_openclaw/` directory within the project root. The `FileSystemStorage` class implements the `StorageProvider` interface. No relational database is used in Version 1.

**Consequences:**

Positive:
- No external database dependency
- Files are human-readable and debuggable
- `.local_openclaw/` is automatically project-scoped
- Simple backup (copy the directory)

Negative:
- No query capability — reads and writes are file-level
- No built-in migration system
- Concurrent write safety is not addressed
- JSON format has size limitations for very large data

**Alternatives Considered:**

- SQLite: rejected — adds a dependency with marginal benefit for current data volume
- PostgreSQL: rejected — violates offline-first, adds operational overhead

---

## Refinement (Sprint 13): Persistence Identity from the Opened Project

**Context:**

Vector persistence (ChromaDB) was originally addressed through configurable paths. A process-starting-directory dependency made the resolved persistence path vary with the backend launch CWD (e.g. `<launch directory>/.local_openclaw/index/chroma`), creating wrong and empty stores.

**Decision:**

Persistence identity is derived exclusively from the opened project:

```
opened Project
    ↓
Project.root_directory / Project.storage_directory
    ↓
project-local persistence
    ↓
same store regardless of process CWD
```

- Chroma persistence resolves to `<project root>/.local_openclaw/index/chroma` (see `app/core/storage/locations.py`).
- `ChromaSettings` exposes only `collection_name` — the persist directory is intentionally **not** configurable.
- Vector stores are resolved per project through the `VectorStoreResolver` interface (`app/indexing/store_resolver.py`); `ProjectChromaStoreResolver` returns `None` for projects that have never been indexed.
- The historical `.repository-intelligence-platform/index/chroma` store (stale data from the former `local-openclaw` path) is not part of the current implementation and was not migrated, rewritten, merged, or deleted.

**Consequences:**

- Launching the backend from any directory yields the same persistence path for the same opened project.
- Queries without an opened project root return no results rather than leaking other projects' data.
- Legacy env keys (`LOC_STORAGE_ROOT_DIRECTORY`, `LOC_CHROMA_PERSIST_DIRECTORY`) are ignored; they are retained in the sample `.env` only as documentation of the former behavior.

**See:** [Sprint 13 freeze report](../sprints/sprint-13.md), [Indexing architecture](../architecture/backend/indexing.md), [Retrieval architecture](../architecture/backend/retrieval.md)
