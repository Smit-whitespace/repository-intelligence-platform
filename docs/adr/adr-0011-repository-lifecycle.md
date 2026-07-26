# ADR-0011: Repository Lifecycle

**Status:** Adopted

**Context:**

A repository transitions through several states: unopened, opened (metadata persisted), scanned (index built), indexed (embeddings stored), and ready for chat. Without a defined lifecycle, the relationships between these states are implicit and error-prone.

**Decision:**

The repository lifecycle is defined as:

1. **Project Open** — `ProjectService.open_project()` validates and persists metadata
2. **Index Build** — `RepositoryService.build_index()` scans and produces a summary
3. **Repository Index** — `IndexingService.index_repository()` loads, chunks, and embeds
4. **Repository Ready** — the repository is ready for retrieval and chat

These stages are sequential and bounded. Each stage is owned by a single service.

**Consequences:**

Positive:
- Clear progression — no ambiguity about what state a repository is in
- Each stage independently testable
- Future background processing can use these stages as task units

Negative:
- No explicit state machine — the sequence is enforced by the orchestrator
- Stage 2 and 3 perform duplicate filesystem scans (see ADR-0014)

**Alternatives Considered:**

- Fully asynchronous pipeline with state persistence: rejected — complexity exceeds current requirements
- Single combined operation: rejected — would violate subsystem boundaries
