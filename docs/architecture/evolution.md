# Architecture Evolution

> **Status:** Complete
> **Sprint Introduced:** Sprint 12.1
> **Last Updated:** Sprint 12.1
> **Reading Time:** 3 minutes
> **Audience:** All contributors
> **Prerequisites:** [System Overview](system-overview.md)

---

## Executive Summary

This document traces how the architecture evolved across major milestones. Each milestone describes what was introduced, why, and what constraints were placed on future work.

---

## Sprint 4 — Repository Indexing

**Objective:** Establish core repository understanding and deterministic chunking.

**Introduced:**
- Repository subsystem (scanner, metadata extractor, document loader, chunker)
- AST-aware Python chunking with line-based fallback
- Deterministic chunk identifiers (SHA-256 content-addressed)
- `RepositoryChunk` domain model

**Key Decisions:**
- Repository understanding is the foundational subsystem
- Chunking is language-agnostic by default, language-specific via registration
- No semantic understanding leaves this subsystem raw

**See:** [ADR-0002 Repository Ownership](../adr/adr-0002-repository-ownership.md), [ADR-0015 Chunking Strategy](../adr/adr-0015-chunking-strategy.md)

---

## Sprint 5 — Retrieval

**Objective:** Introduce semantic search over indexed repository content.

**Introduced:**
- Indexing subsystem (embedding generation, `IndexedChunk`)
- Retrieval subsystem (`SearchQuery`, `SearchHit`, `SearchResponse`)
- `EmbeddingProvider` interface
- `VectorStore` interface
- ChromaDB adapter
- `RepositoryIndexer` class

**Key Decisions:**
- Retrieval is independent of indexing
- `SearchHit` is a projection, separate from `IndexedChunk`
- Embedding provider and vector store are abstract interfaces

**See:** [ADR-0003 Indexing Ownership](../adr/adr-0003-indexing-ownership.md), [ADR-0004 Retrieval Boundaries](../adr/adr-0004-retrieval-boundaries.md), [ADR-0006 ChromaVectorStore](../adr/adr-0006-chromadb-vector-store.md), [ADR-0008 Search Projection](../adr/adr-0008-search-projection.md)

---

## Sprint 6 — Chat and Context Assembly

**Objective:** Introduce repository-aware conversational AI.

**Introduced:**
- `ChatService` (retrieval + context assembly + LLM)
- `DefaultContextAssembly` (builds prompts from retrieved context)
- `ChatPrompt` model
- `ChatProvider` interface
- `OllamaChatProvider` implementation

**Key Decisions:**
- Chat never indexes — it only retrieves
- Context assembly is a separate interface from chat
- Prompt construction is owned by context assembly, not chat

**See:** [ADR-0012 Repository-aware Chat Pipeline](../adr/adr-0012-repository-aware-chat.md), [ADR-0017 Prompt Construction Strategy](../adr/adr-0017-prompt-construction.md)

---

## Sprint 8 — Rollback

**Objective:** Provide safe editing with snapshot-based rollback.

**Introduced:**
- Editing subsystem (changeset generation, application)
- Snapshot mechanism (pre-edit file capture)
- `ChangeApplier` for safe file modification
- `SnapshotStore` for persistence

**Key Decisions:**
- Editing is the sole owner of repository modification
- All modifications are reversible via snapshots
- Editing never performs repository analysis

**See:** [ADR-0010 Filesystem Persistence](../adr/adr-0010-filesystem-persistence.md)

---

## Sprint 9 — Stabilization

**Objective:** Cross-subsystem stabilization and boundary hardening.

**Key Decisions:**
- Dependency injection centralized in `providers.py`
- Subsystem boundaries tightened
- Public interfaces frozen for V1
- Validation gates established (Ruff + MyPy + Pytest)

**See:** [ADR-0005 Dependency Injection](../adr/adr-0005-dependency-injection.md)

---

## Sprint 12.1 — ProjectInitializationService

**Objective:** Automate project initialization on open — wire repository indexing into the project lifecycle.

**Introduced:**
- `ProjectInitializationService` — orchestration layer
- `open_project()` calls `ProjectService` → `RepositoryService.build_index()` → `IndexingService.index_repository()`
- Provider functions for `RepositoryDocumentLoader`, `RepositoryChunker`, `RepositoryIndexer`, `IndexingService`

**Key Decisions:**
- Orchestration is a service, not business logic
- `build_index()` and `index_repository()` are both called — they are independent operations

**See:** [ADR-0009 ProjectInitializationService](../adr/adr-0009-project-initialization-service.md), [ADR-0011 Repository Lifecycle](../adr/adr-0011-repository-lifecycle.md), [ADR-0013 Initialization Orchestration](../adr/adr-0013-initialization-orchestration.md), [ADR-0014 Repository Scan Ownership](../adr/adr-0014-repository-scan-ownership.md)

---

## Next: Sprint 12.2 — Chat Integration

*Planned — see [Roadmap](../../roadmap/).*

---

## Related Documents

| Document | Link |
|----------|------|
| System Overview | [system-overview.md](system-overview.md) |
| Roadmap | [roadmap/](../../roadmap/) |
| Sprint 12.1 | [sprints/sprint-12.1.md](../../sprints/sprint-12.1.md) |
