# Document 0 — Project Manifest

**Local OpenClaw (LOC)**
**Executive Project Dashboard**
**Status:** Authoritative
**Document Version:** 3.0
**Last Updated:** End of Sprint 4 RC-4 Implementation Session

---

# 1. Project Identity

| Item                        | Value                                                     |
| --------------------------- | --------------------------------------------------------- |
| **Project Name**            | Local OpenClaw (LOC)                                      |
| **Purpose**                 | Offline-first, repository-aware AI coding assistant       |
| **Current Product Version** | Version 1 (In Development)                                |
| **Current Sprint**          | Sprint 4 — Repository Intelligence & Retrieval Foundation |
| **Current Release**         | RC-4 (Release Candidate)                                  |
| **Current Phase**           | Implementation Stabilization                              |

---

# 2. Document Hierarchy

This document is the **executive dashboard** for the project.

Its purpose is to provide a concise, high-level view of the project's current state and direct readers to the appropriate detailed documentation.

The complete documentation hierarchy is:

* **Document 0 — Project Manifest (this document)**
  Executive dashboard and project front page.

* **Document 1 — Project Foundation**
  Canonical project definition, frozen architecture, accepted ADRs, public interfaces, and folder structure.

* **Document 2 — Engineering State**
  Current implementation status, frozen files, engineering progress, and implementation queue.

* **Document 3 — Release State**
  Technical debt, release criteria, validation requirements, and Definition of Done.

* **Document 4 — Continuation Package**
  Canonical continuation instructions for implementation in a new development session.

* **Document 5 — Supplementary Engineering Knowledge**
  Engineering conventions, lessons learned, known issues, remaining unknowns, and implementation guidance.

**Authority Rule**

This document is intentionally concise.

If any discrepancy exists between this document and Documents **1–5**, the detailed documents take precedence.

---

# 3. Current Status Dashboard

| Area               | Status                 |
| ------------------ | ---------------------- |
| **Architecture**   | **Frozen**             |
| **Implementation** | **In Progress**        |
| **Testing**        | **In Progress**        |
| **Validation**     | **Pending**            |
| **Documentation**  | **In Progress**        |
| **Release**        | **RC-4 Stabilization** |

---

# 4. Current Objective

Sprint 4 is dedicated to delivering a production-ready **Repository Intelligence & Retrieval Foundation**.

The remaining work consists of:

* completing the remaining retrieval-related test suites,
* validating the implementation,
* correcting only verified implementation defects,
* generating the release documentation,
* and freezing Sprint 4.

No expansion of project scope is permitted during this sprint.

---

# 5. Current Implementation Focus

Execution order is fixed for the remainder of Sprint 4:

1. Implement `tests/indexing/test_chroma_store.py`
2. Implement `tests/indexing/test_retrieval_service.py`
3. Execute repository validation
4. Stabilize verified defects
5. Validate repository metadata round-trip behavior
6. Generate Sprint 4 release documentation
7. Generate Sprint 4 checkpoint
8. Freeze Sprint 4

---

# 6. Current Working File

**Current Implementation Target**

```text
backend/tests/indexing/test_chroma_store.py
```

Implementation should continue from this file until it is complete.

Only after this file has been completed and stabilized should work proceed to the next item in the implementation queue.

---

# 7. Known Good (Frozen Architecture & Stable Components)

The following components have undergone architectural review and implementation review and should be considered **stable for Sprint 4**.

"Known Good" means:

* architecture is frozen,
* subsystem ownership is established,
* responsibilities are defined,
* public interfaces are stable,
* implementation has been reviewed.

It **does not** imply that every implementation has already been runtime validated.

Compiler, type-checker, test, or runtime issues discovered during validation remain valid stabilization work.

### Stable Architecture

* Overall system architecture
* Repository subsystem
* Indexing subsystem
* Retrieval subsystem
* Persistence architecture
* API architecture

### Stable Subsystem Boundaries

* Repository
* Repository Chunking
* Metadata Extraction
* Document Loading
* Indexing
* Embedding
* Retrieval
* Vector Store

### Stable Public Interfaces

* Repository domain models
* Indexing models
* Retrieval models
* `EmbeddingProvider`
* `VectorStore`

### Stable Reviewed Implementation

* Repository subsystem
* Repository parsing
* Repository chunking
* Repository indexing
* Retrieval models
* Chroma adapter *(pending runtime validation only)*
* Retrieval service *(pending runtime validation only)*

---

# 8. Validation Status

| Validation                         | Status  |
| ---------------------------------- | ------- |
| **Ruff**                           | Pending |
| **MyPy**                           | Pending |
| **Pytest**                         | Pending |
| **Metadata Round-Trip Validation** | Pending |

Validation results determine stabilization work.

No implementation changes should be made solely in anticipation of potential validation failures.

---

# 9. Current Release Blockers

Sprint 4 cannot be frozen until all of the following have been completed:

* Remaining retrieval test suites
* Repository validation (Ruff, MyPy, Pytest)
* Stabilization of verified defects
* Metadata round-trip validation
* Sprint 4 release documentation
* Sprint 4 checkpoint

---

# 10. Accepted Technical Debt

Current accepted technical debt is intentionally minimal.

**TD-001**

Repository metadata round-trip behavioral testing is deferred until runtime behavior has been validated.

Refer to **Document 3 — Release State** for the authoritative technical debt register.

---

# 11. Explicitly Out of Scope

The following categories are intentionally excluded from Sprint 4:

* Architecture redesign
* New ADRs
* Feature expansion
* New abstractions
* Performance optimization without evidence
* Git integration
* Authentication
* Cloud synchronization
* Plugin framework
* Internet-enabled features
* Context assembly implementation
* Memory redesign
* Alternative retrieval backends
* SQL database integration
* Opportunistic refactoring

---

# 12. Never Reopen During Sprint 4

The following decisions are frozen:

* Overall architecture
* Repository ownership
* Indexing ownership
* Retrieval ownership
* ChromaDB ownership of vector persistence and semantic search (ADR-0007)
* Context Assembly deferred to a future subsystem (ADR-0008)
* `SearchHit` as a retrieval projection independent of `IndexedChunk` (ADR-ARB-001)
* Frozen public interfaces
* Version 1 feature scope

These decisions remain closed unless an explicit architecture review is requested.

---

# 13. Escalation Rule

Implementation should proceed within the boundaries of the frozen architecture.

If a verified issue can be resolved without changing an accepted ADR, frozen public interface, or subsystem boundary, it should be treated as normal stabilization work.

If a verified issue **cannot** be resolved without violating those constraints:

1. Stop implementation.
2. Document the issue and supporting evidence.
3. Request an architecture review.
4. Do not redesign the system during implementation.

---

# 14. Project Principles

The engineering philosophy of Local OpenClaw is intentionally conservative:

* **Offline-first** by design.
* **Clear subsystem ownership** over shared responsibilities.
* **Maintainability before extensibility.**
* **Simplicity over unnecessary abstraction.**
* Introduce abstractions **only** when justified by multiple implementations or demonstrated need.
* Keep **Version 1 intentionally small and cohesive.**
* Preserve frozen public interfaces throughout Sprint 4.
* Prefer explicit, readable implementations over clever or highly generalized solutions.
* Stabilize before extending functionality.

These principles should guide implementation decisions whenever multiple acceptable solutions exist.

---

# 15. Primary Engineering Rules

The following engineering process applies throughout Sprint 4:

* Work on one implementation task at a time.
* Audit before modifying code.
* Prefer the smallest correct change.
* Preserve subsystem boundaries.
* Preserve frozen public interfaces.
* Do not introduce speculative abstractions.
* Do not perform opportunistic refactoring.
* Validate using:

  1. Ruff
  2. MyPy
  3. Pytest
* Treat only verified failures as stabilization work.
* Keep implementation aligned with accepted ADRs.

---

# 16. Reference Documents
| -------------------------------------------------------------------------------------------------------------------------------------|
|           Document                            |              Responsibility                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------|
| **Document 1 — Project Foundation**           | Defines the project, frozen architecture, accepted ADRs, public interfaces,          |
|                                               | and folder structure.                                                                |
| -------------------------------------------------------------------------------------------------------------------------------------|
| **Document 2 — Engineering State**            | Defines implementation status, file states, completed work,                          |
|                                               | remaining implementation queue, and dependencies.                                    |
| -------------------------------------------------------------------------------------------------------------------------------------|
| **Document 3 — Release State**                | Defines technical debt, deferred work, release blockers, validation checklist,       |
|                                               | definition of Done, and release criteria.                                            |
| -------------------------------------------------------------------------------------------------------------------------------------|
| **Document 4 — Continuation Package**         | Provides the canonical implementation prompt for continuing Sprint 4 in              |
|                                               | a new development session.                                                           |
| -------------------------------------------------------------------------------------------------------------------------------------|
| **Document 5 — Supplementary Engineering**    | Captures engineering conventions, known issues, remaining unknowns,                  |
| **Knowledge**                                 | lessons learned, coding philosophy, and practical implementation guidance.           |
| -------------------------------------------------------------------------------------------------------------------------------------|
---

# 17. Manifest Summary

**Architecture:** Frozen

**Implementation:** Final stabilization phase

**Current Priority:** Complete remaining test suites → validate → stabilize verified defects → generate release documentation → freeze Sprint 4

**Project Scope:** Stable and intentionally constrained. No architectural redesign, feature expansion, or speculative refactoring is permitted during Sprint 4.

## Sprint 4 Success Criteria

Sprint 4 is complete **only when all of the following are true**:

* ☐ Remaining production implementation is complete
* ☐ Remaining retrieval test suites are implemented
* ☐ Ruff passes
* ☐ MyPy passes
* ☐ Pytest passes
* ☐ Repository metadata round-trip behavior has been validated
* ☐ Sprint 4 release documentation has been generated
* ☐ Sprint 4 checkpoint has been generated
* ☐ Sprint 4 has been formally declared **Frozen**

---

**Document Status:** **Authoritative**

This manifest serves as the executive dashboard and front page of the Local OpenClaw project. It is designed to provide a complete understanding of the project's current state within minutes while directing readers to Documents 1–5 for authoritative technical detail. During Sprint 4, this document should remain stable and change only when the project's authoritative state changes.
