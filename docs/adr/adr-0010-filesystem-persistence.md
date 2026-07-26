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
