# ADR-0002: Repository Ownership

**Status:** Adopted

**Context:**

Multiple subsystems need to understand repository structure — indexing requires files, retrieval requires context, chat requires understanding. Without clear ownership, scanning and analysis logic would scatter across subsystems, creating duplication and inconsistency.

**Decision:**

The Repository subsystem is the sole owner of repository understanding. No other subsystem may scan the filesystem, extract metadata, or generate chunks. Downstream subsystems consume `RepositoryChunk` and `RepositoryEntry` but never produce them.

**Consequences:**

Positive:
- Single authority for repository structure
- Consistent chunking and metadata across all consumers
- Clear dependency direction

Negative:
- Indexing and retrieval are coupled to repository output format
- The repository scan is a bottleneck for all downstream operations

**Alternatives Considered:**

- Per-subsystem scanning: rejected — would duplicate logic and produce inconsistent results
- Shared scanning library: rejected — close to current approach but blurs ownership
