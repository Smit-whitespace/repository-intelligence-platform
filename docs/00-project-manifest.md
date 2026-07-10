> **Document Status**
>
> This document reflects the authoritative Sprint 4 project state. Minor wording or synchronization updates may occur in future revisions without changing the project's engineering state or architectural decisions. Unless explicitly superseded, this document should be treated as authoritative.

# Document 0 — Project Manifest

**Local OpenClaw (LOC)**
**Executive Project Dashboard**
**Status:** Authoritative
**Document Version:** 3.0
**Last Updated:** Sprint 4 completion/freeze.

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
| **Implementation** | **Complete**        |
| **Testing**        | **Complete**        |
| **Validation**     | **Complete**            |
| **Documentation**  | **Complete**        |
| **Release**        | **RC-4 Frozen** |

---

# 4. Current Objective

Sprint 4 is dedicated to delivering a production-ready **Repository Intelligence & Retrieval Foundation**.

-Sprint 4 successfully delivered the Repository Intelligence & Retrieval Foundation.
-All Sprint 4 engineering objectives have been completed.
-Sprint 4 has been frozen.
-No additional implementation work belongs to Sprint 4.

No expansion of project scope was permitted during this sprint.

---

# 5. Current Implementation Focus

Execution order is fixed for the remainder of Sprint 4:

-Repository Intelligence is complete.
-Semantic Indexing is complete.
-ChromaVectorStore implementation is complete.
-Retrieval Foundation is complete.
-Sprint 4 implementation has concluded.

No new implementation sequence should be introduced.

---

# 6. Current Working File

**Current Implementation Target**

There is no active Sprint 4 implementation target.

Sprint 4 has been successfully completed and frozen.

Future implementation targets will be identified by subsequent engineering planning outside the scope of this manifest.

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
* Chroma adapter 
* Retrieval service 

---

# 8. Validation Status

| Validation                         | Status  |
| ---------------------------------- | ------- |
| **Ruff**                           | Pass |
| **MyPy**                           | Pass |
| **Pytest**                         | Pass |
| **Metadata Round-Trip Validation** | Pass |

Validation results determine stabilization work.

No implementation changes should be made solely in anticipation of potential validation failures.

---

# 9. Current Release Blockers

There are no remaining Sprint 4 release blockers.

Sprint 4 has satisfied its release criteria and has been formally frozen.

---

# 10. Accepted Technical Debt

Current accepted technical debt is intentionally minimal.

**TD-001**

There is no remaining accepted Sprint 4 engineering technical debt.

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

**Implementation:** Sprint 4 implementation completed successfully.

**Current Priority:** None as Sprint 4 implementation is completed successfully.

Repository Intelligence & Retrieval Foundation delivered.

Sprint 4 formally frozen.

**Project Scope:** Stable and intentionally constrained. No architectural redesign, feature expansion, or speculative refactoring was permitted during Sprint 4.

## Sprint 4 Success Criteria

Sprint 4 is complete **only when all of the following are true**: (ignore content in this bracket::: ☑ ☐ )

* ☑ Remaining production implementation is complete
* ☑ Remaining retrieval test suites are implemented
* ☑ Ruff passes
* ☑ MyPy passes
* ☑ Pytest passes
* ☑ Repository metadata round-trip behavior has been validated
* ☑ Sprint 4 release documentation has been generated
* ☑ Sprint 4 checkpoint has been generated
* ☑ Sprint 4 has been formally declared **Frozen**

---

**Document Status:** **Authoritative**

This manifest serves as the executive dashboard and front page of the Local OpenClaw project. It is designed to provide a complete understanding of the project's current state within minutes while directing readers to Documents 1–5 for authoritative technical detail. 

Sprint 4 has successfully delivered the Repository Intelligence & Retrieval Foundation, satisfied all validation requirements, generated the required release documentation, and has been formally declared Frozen. The Project Manifest now reflects the finalized Sprint 4 engineering state.
