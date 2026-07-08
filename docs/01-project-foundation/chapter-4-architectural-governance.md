# Document 1 — Project Foundation

## Chapter 4 — Architectural Governance (Part A)

**Local OpenClaw (LOC)**
**Software Architecture Specification (SAS)**
**Document Status:** Authoritative
**Document:** 4 of 5 — Chapter 4 (Part A of IV)

---

# Chapter Metadata

| Property          | Value                                                                   |
| ----------------- | ----------------------------------------------------------------------- |
| **Document**      | Project Foundation                                                      |
| **Chapter**       | Chapter 4 — Architectural Governance                                    |
| **Scope**         | Permanent Architecture Governance                                       |
| **Stability**     | Frozen (subject only to future ADRs or governance policy revisions)     |
| **Depends On**    | Document 0 — Project Manifest, Document 1 — Chapters 1–3                |
| **Referenced By** | Document 2 — Engineering State, Document 3 — Release State, Future ADRs |
| **Last Updated**  | Sprint 4 RC-4                                                           |

---

# 1. Governance Overview

## 1.1 Purpose

This chapter defines the governance model that preserves the long-term architectural integrity of Local OpenClaw.

Where previous chapters establish:

* **why** the project exists,
* **how** it is architected,
* **what** Version 1 delivers,

this chapter defines **how architectural consistency is maintained as the project evolves**.

It establishes the permanent rules governing architectural ownership, interface stability, dependency management, documentation, and architectural decision-making.

---

## 1.2 Scope

Architectural governance applies to every subsystem, interface, implementation, and future enhancement within Local OpenClaw.

Its objectives are to:

* preserve subsystem ownership,
* prevent architectural drift,
* maintain stable public interfaces,
* document architectural decisions,
* ensure long-term maintainability.

Governance exists to protect architectural quality without unnecessarily restricting implementation.

---

## 1.3 Guiding Philosophy

Architectural governance follows five fundamental principles:

1. **Architecture is intentional.**
2. **Ownership is explicit.**
3. **Interfaces are stable.**
4. **Evolution is incremental.**
5. **Architectural change is deliberate.**

Every governance rule defined in this chapter derives from one or more of these principles.

---

# 2. Architecture Decision Records (ADRs)

## 2.1 Purpose

Architecture Decision Records (ADRs) are the authoritative mechanism for documenting significant architectural decisions.

An ADR records:

* the architectural problem,
* the accepted decision,
* the rationale,
* the architectural consequences.

Once accepted, an ADR becomes part of the permanent architectural specification.

---

## 2.2 When an ADR is Required

An ADR is required whenever a proposed change affects one or more of the following:

* subsystem ownership,
* dependency direction,
* public interfaces,
* architectural invariants,
* architectural principles,
* product scope,
* persistence architecture,
* API contracts,
* cross-subsystem communication.

Routine implementation decisions do not require ADRs.

---

## 2.3 ADR Lifecycle

Every Architecture Decision Record progresses through the following lifecycle:

```text
Proposed
    │
    ▼
Reviewed
    │
    ▼
Accepted
    │
    ▼
Implemented
    │
    ▼
Frozen
```

Only **Accepted** ADRs may influence implementation.

Rejected or superseded ADRs do not define the architecture.

---

## 2.4 ADR Contents

Each ADR should contain:

* Identifier
* Title
* Status
* Context
* Decision
* Rationale
* Consequences
* Impacted Subsystems
* Impacted Public Interfaces
* References

This structure provides sufficient context for future maintainers without requiring historical reconstruction.

---

# 3. Accepted Architecture Decision Records

The following ADRs constitute the authoritative architectural decisions for Version 1.

---

## ADR-0007 — Vector Store Ownership

### Status

**Accepted / Frozen**

### Decision

The Vector Store abstraction defines the architectural contract for semantic vector persistence.

Concrete implementations are responsible for storing and querying semantic vector representations while remaining independent of higher-level retrieval workflows.

Retrieval interacts with vector persistence exclusively through the published vector storage interface.

### Rationale

This preserves:

* subsystem independence,
* storage replaceability,
* retrieval abstraction,
* separation between indexing and retrieval responsibilities.

### Impacted Areas

* Indexing
* Retrieval
* Persistence

---

## ADR-0008 — Retrieval Projection Model

### Status

**Accepted / Frozen**

### Decision

The Retrieval subsystem exposes retrieval-specific projection models rather than indexing implementation models.

Retrieval contracts remain independent of embedding-aware indexing structures.

### Rationale

This preserves:

* subsystem ownership,
* public interface stability,
* separation between indexing and retrieval.

### Impacted Areas

* Retrieval
* Indexing
* Public retrieval interfaces

---

## ADR-ARB-001 — Retrieval–Indexing Decoupling

### Status

**Accepted / Frozen**

### Decision

Embedding-aware indexing models remain internal to the Indexing subsystem.

Retrieval exposes only retrieval-facing projections containing the repository information required by retrieval consumers.

Embedding vectors do not leave the Indexing subsystem.

### Rationale

The review identified accidental coupling between retrieval contracts and indexing implementation models.

Removing that coupling:

* simplifies subsystem ownership,
* prevents implementation leakage,
* preserves long-term architectural independence.

### Impacted Areas

* Retrieval
* Indexing
* Search models
* VectorStore interface

---

# 4. Architectural Change Management

## 4.1 Principle

Architecture evolves through deliberate decisions rather than incidental implementation.

No implementation change should silently redefine architectural behavior.

---

## 4.2 Permitted Changes

The following changes may occur without introducing a new ADR provided they preserve existing architectural behavior:

* implementation improvements,
* performance optimizations,
* bug fixes,
* additional tests,
* documentation clarifications,
* internal refactoring,
* new implementations behind existing abstractions.

These changes must not alter public architectural behavior.

---

## 4.3 Changes Requiring an ADR

A new ADR is required before implementing changes that affect:

* subsystem responsibilities,
* ownership boundaries,
* dependency direction,
* architectural principles,
* public contracts,
* architectural invariants,
* Version 1 product scope.

Implementation must not precede architectural approval.

---

## 4.4 Backward Compatibility

Architectural evolution should preserve backward compatibility wherever practical.

Breaking architectural contracts should occur only when:

* the existing contract is demonstrably incorrect,
* architectural improvement clearly outweighs migration cost,
* or long-term maintainability requires correction.

Such changes require explicit architectural approval through an ADR.

---

# 5. Governance Objectives

Architectural governance exists to ensure that Local OpenClaw remains:

* understandable,
* maintainable,
* modular,
* extensible,
* internally consistent.

Governance is intended to preserve architectural quality while allowing implementation to evolve within clearly defined boundaries.

---

## Part A Status

This part establishes the governance foundation of Local OpenClaw by defining:

* the purpose of architectural governance,
* the role of Architecture Decision Records,
* the accepted and frozen ADRs,
* architectural change management principles.

These governance mechanisms provide the formal process through which future architectural evolution may occur while preserving the integrity of the Software Architecture Specification.


# Document 1 — Project Foundation

## Chapter 4 — Architectural Governance (Part B)

**Local OpenClaw (LOC)**
**Software Architecture Specification (SAS)**
**Document Status:** Authoritative
**Document:** 4 of 5 — Chapter 4 (Part B of IV)

---

# 6. Subsystem Ownership

## 6.1 Purpose

Architectural ownership defines which subsystem is responsible for each domain capability within Local OpenClaw.

Every architectural responsibility shall have **exactly one owning subsystem**.

Exclusive ownership:

* prevents duplicated behavior,
* reduces coupling,
* clarifies implementation responsibility,
* simplifies future architectural evolution.

Ownership is defined by responsibility rather than implementation.

---

## 6.2 Ownership Principles

The following principles govern subsystem ownership:

### Exclusive Ownership

Every responsibility has a single authoritative owner.

Shared ownership is considered an architectural defect because it creates ambiguity regarding where behavior should reside.

---

### Responsibility Before Technology

Ownership is assigned according to business responsibility, not implementation technology.

Replacing a framework or storage mechanism must not alter subsystem ownership.

---

### Stable Boundaries

Subsystem boundaries should remain stable over time.

Responsibilities may evolve within a subsystem, but ownership should not migrate without an accepted ADR.

---

### Clear Dependencies

Subsystems may depend on each other's published interfaces but must never assume ownership of another subsystem's responsibilities.

---

# 7. Subsystem Ownership Matrix

The following matrix defines the authoritative ownership of architectural responsibilities.

| Responsibility                  | Owning Subsystem |
| ------------------------------- | ---------------- |
| Repository discovery            | Repository       |
| Filesystem traversal            | Repository       |
| Ignore rule processing          | Repository       |
| Repository metadata extraction  | Repository       |
| Document loading                | Repository       |
| Language-aware parsing          | Repository       |
| Repository chunk generation     | Repository       |
| Deterministic chunk identifiers | Repository       |
| Embedding generation            | Indexing         |
| IndexedChunk construction       | Indexing         |
| Vector persistence              | Indexing         |
| Semantic indexing               | Indexing         |
| Query embedding generation      | Retrieval        |
| Semantic search orchestration   | Retrieval        |
| Retrieval projections           | Retrieval        |
| Search response construction    | Retrieval        |
| Persistent contextual knowledge | Memory           |
| Session context                 | Memory           |
| Working context                 | Memory           |
| Architectural memory            | Memory           |
| Repository modification         | Editing          |
| Patch application               | Editing          |
| Snapshot creation               | Editing          |
| Diff generation                 | Editing          |
| Rollback                        | Editing          |
| API contracts                   | API              |
| Request validation              | API              |
| Response serialization          | API              |
| Streaming communication         | API              |
| Background task exposure        | API              |
| Durable storage                 | Persistence      |
| Configuration persistence       | Persistence      |
| Snapshot persistence            | Persistence      |
| Vector storage infrastructure   | Persistence      |
| Frontend presentation           | Frontend         |
| User interaction                | Frontend         |
| Client state                    | Frontend         |

This matrix is normative.

When ownership is unclear during implementation, this matrix takes precedence unless modified through an accepted ADR.

---

# 8. Frozen Public Interfaces

## 8.1 Purpose

Public interfaces define the contractual boundaries between architectural subsystems.

They establish the information that may cross subsystem boundaries while preventing implementation details from leaking across architectural layers.

Public interfaces are considered stable architectural assets.

---

## 8.2 Public Interface Categories

Local OpenClaw defines four categories of public interfaces:

| Category            | Purpose                                          |
| ------------------- | ------------------------------------------------ |
| Domain Models       | Represent information shared between subsystems. |
| Service Interfaces  | Define subsystem capabilities.                   |
| Provider Interfaces | Abstract infrastructure services.                |
| API Contracts       | Define communication with external clients.      |

These categories collectively define the architectural communication surface.

---

## 8.3 Domain Model Interfaces

The following models constitute stable architectural contracts between subsystems.

### Repository

* RepositoryEntry
* RepositoryDocument
* RepositoryChunk
* RepositoryChunkMetadata
* ChunkBoundary

---

### Indexing

* EmbeddingVector
* IndexedChunk *(internal to the Indexing subsystem; not exposed beyond its architectural boundary)*
* IndexingResult

---

### Retrieval

* SearchQuery
* SearchHit
* SearchResult
* SearchResponse

---

### Editing

Public editing models are defined by the Editing subsystem as part of its stable interface.

---

### Memory

Public memory models are defined by the Memory subsystem as implementation progresses while preserving the architectural boundaries established in Chapter 2.

---

## 8.4 Service Interfaces

The following service-level interfaces define subsystem capabilities.

Examples include:

* Repository services
* Indexing services
* Retrieval services
* Editing services
* Memory services

Concrete implementations remain internal to the owning subsystem.

---

## 8.5 Provider Interfaces

Infrastructure dependencies are exposed through provider interfaces.

Representative examples include:

* EmbeddingProvider
* VectorStore
* StorageProvider

Provider interfaces allow infrastructure implementations to evolve independently of business logic.

---

## 8.6 API Interfaces

External communication occurs exclusively through versioned API contracts.

Version 1 includes:

* REST endpoints
* Server-Sent Events (SSE)
* Background task endpoints
* Standardized error objects

Transport mechanisms remain separate from domain models.

---

# 9. Interface Stability Policy

## 9.1 Stable by Default

Public interfaces are stable unless explicitly superseded through an accepted ADR.

Consumers should be able to depend upon published contracts without knowledge of internal implementation.

---

## 9.2 Internal Models

Implementation models remain private to the owning subsystem.

Examples include:

* embedding-aware indexing structures,
* storage-specific persistence objects,
* provider-specific response models.

These models are intentionally excluded from cross-subsystem contracts.

---

## 9.3 Backward Compatibility

Public interface evolution should preserve backward compatibility wherever practical.

Breaking changes require explicit architectural justification and documentation.

---

# 10. Architectural Compliance Rules

Every implementation should satisfy the following compliance requirements.

---

## Rule 1 — Respect Ownership

Implement behavior within the subsystem that owns the corresponding responsibility.

Ownership shall not migrate implicitly through implementation.

---

## Rule 2 — Preserve Boundaries

Subsystems communicate only through published public interfaces.

Internal implementation details must remain encapsulated.

---

## Rule 3 — Maintain Dependency Direction

Dependencies shall follow the hierarchy established in Chapter 2.

Upward dependencies are prohibited.

---

## Rule 4 — Protect Public Interfaces

Implementation changes shall not silently alter published contracts.

Interface evolution requires deliberate architectural review.

---

## Rule 5 — Avoid Responsibility Duplication

Behavior shall not be implemented in multiple subsystems.

If ownership becomes ambiguous, architecture must be clarified before implementation continues.

---

## Rule 6 — Keep Business Logic Independent

Business logic belongs exclusively to domain subsystems.

Infrastructure components provide capabilities but do not own domain behavior.

---

## Rule 7 — Preserve Deterministic Behavior

Repository understanding should remain deterministic wherever practical.

Equivalent repository states should produce equivalent repository representations.

---

## Rule 8 — Minimize Coupling

Dependencies should expose only the information required to satisfy architectural responsibilities.

Implementation details must remain private.

---

## Part B Status

This part defines the governance of subsystem ownership and architectural interfaces by establishing:

* the authoritative subsystem ownership model,
* the ownership matrix for architectural responsibilities,
* the categories of frozen public interfaces,
* interface stability expectations,
* and the architectural compliance rules that govern implementation.

Together with Part A, these sections provide the structural governance required to preserve architectural consistency as Local OpenClaw evolves.


# Document 1 — Project Foundation

## Chapter 4 — Architectural Governance (Part C)

**Local OpenClaw (LOC)**
**Software Architecture Specification (SAS)**
**Document Status:** Authoritative
**Document:** 4 of 5 — Chapter 4 (Part C of IV)

---

# 11. Dependency Governance

## 11.1 Purpose

Dependency governance ensures that architectural relationships remain consistent throughout the lifetime of the project.

While subsystem ownership defines **who is responsible** for a capability, dependency governance defines **how subsystems are permitted to interact**.

Maintaining disciplined dependency relationships prevents architectural erosion, reduces coupling, and allows individual subsystems to evolve independently.

---

## 11.2 Architectural Dependency Hierarchy

Local OpenClaw follows a layered dependency model.

```text
Frontend
        │
        ▼
API
        │
        ▼
Application Services
        │
        ▼
Repository   Indexing   Retrieval   Memory   Editing
        │         │          │          │         │
        └─────────┴──────────┴──────────┴─────────┘
                          │
                          ▼
                   Persistence
```

This hierarchy defines **permitted dependency direction**, not implementation order.

Every dependency must move downward through the architecture.

---

## 11.3 Dependency Rules

### Rule 1 — Downward Dependencies Only

A subsystem may depend only upon architectural layers below it.

Lower layers must never depend upon higher layers.

---

### Rule 2 — Public Interfaces Only

Subsystems communicate exclusively through published public interfaces.

Internal implementation classes, helper functions, storage representations, and provider-specific models shall remain private.

---

### Rule 3 — No Peer Implementation Dependencies

Peer subsystems shall not access each other's internal implementations.

Communication between peers occurs only through their published contracts.

For example:

* Retrieval may consume repository models.
* Retrieval shall not access repository implementation details.

---

### Rule 4 — Infrastructure Isolation

Infrastructure dependencies remain isolated behind provider interfaces.

Business logic should not directly depend upon implementation-specific technologies.

Examples include:

* AI providers
* Vector databases
* Filesystem implementations

---

### Rule 5 — No Circular Dependencies

Architectural dependencies shall remain acyclic.

Circular subsystem dependencies indicate incorrect ownership or misplaced responsibilities.

---

## 11.4 Dependency Validation

Dependency correctness should be continuously verified through:

* architectural review,
* implementation review,
* static analysis where practical,
* code review,
* release validation.

Architectural violations should be corrected immediately upon discovery.

---

# 12. Documentation Governance

## 12.1 Purpose

Documentation is considered an architectural asset rather than a secondary project artifact.

Every architectural document contributes to the long-term maintainability of Local OpenClaw.

Documentation should remain synchronized with accepted architectural decisions.

---

## 12.2 Documentation Hierarchy

The project documentation is organized into complementary documents with distinct responsibilities.

| Document   | Primary Responsibility               |
| ---------- | ------------------------------------ |
| Document 0 | Executive project overview           |
| Document 1 | Permanent architecture specification |
| Document 2 | Current engineering state            |
| Document 3 | Release readiness and validation     |
| Document 4 | Implementation continuation package  |
| Document 5 | Supplementary engineering knowledge  |

Each document serves a unique purpose.

Duplication between documents should be minimized.

---

## 12.3 Source of Truth

The authoritative source for permanent architectural decisions is **Document 1 — Project Foundation**.

Engineering status, release readiness, implementation progress, and technical debt are documented separately to preserve the long-term stability of the architecture specification.

---

## 12.4 Documentation Evolution

Documentation evolves according to its purpose.

### Permanent Documentation

Examples:

* architectural principles,
* subsystem ownership,
* public interfaces,
* dependency rules.

These documents change infrequently.

---

### Operational Documentation

Examples:

* implementation progress,
* stabilization work,
* release validation,
* technical debt.

These documents evolve continuously during development.

Separating these concerns prevents architectural documentation from becoming obsolete.

---

## 12.5 Documentation Quality Principles

Project documentation should be:

* accurate,
* internally consistent,
* implementation-independent where appropriate,
* concise,
* maintainable,
* version aware.

Documentation should explain architectural intent rather than implementation mechanics whenever practical.

---

# 13. Architecture Review Process

## 13.1 Purpose

Architecture review exists to ensure that significant changes preserve the long-term integrity of the system.

It provides a structured mechanism for evaluating architectural impact before implementation begins.

---

## 13.2 Review Triggers

Architecture review should occur whenever a proposed change affects:

* subsystem ownership,
* architectural principles,
* dependency direction,
* public interfaces,
* architectural invariants,
* Version 1 product scope.

Routine implementation work does not require architectural review.

---

## 13.3 Review Criteria

Architectural review evaluates whether a proposed change:

* preserves subsystem cohesion,
* reduces or increases coupling,
* maintains dependency direction,
* respects ownership boundaries,
* protects public interfaces,
* improves long-term maintainability.

A proposal should be accepted only when the architectural benefit clearly outweighs the associated complexity.

---

## 13.4 Evidence-Based Decision Making

Architectural decisions should be supported by implementation evidence rather than hypothetical future requirements.

Evidence may include:

* implementation constraints,
* verified coupling,
* demonstrated duplication,
* interface inconsistencies,
* maintenance concerns.

Speculative optimization should not drive architectural evolution.

---

# 14. Architectural Compliance Verification

## 14.1 Purpose

Compliance verification ensures that the implemented system continues to conform to the architecture defined by this Software Architecture Specification.

Architecture is considered complete only when implementation aligns with its documented intent.

---

## 14.2 Verification Objectives

Compliance verification should confirm:

* subsystem ownership remains intact,
* dependency direction is preserved,
* public interfaces remain stable,
* architectural invariants continue to hold,
* implementation responsibilities remain correctly assigned.

---

## 14.3 Verification Activities

Typical verification activities include:

* architecture reviews,
* implementation audits,
* interface reviews,
* dependency analysis,
* static analysis,
* release validation.

These activities complement one another and collectively provide confidence in architectural correctness.

---

## 14.4 Non-Compliance

When implementation diverges from the architecture, the discrepancy should be classified as one of the following:

| Classification        | Description                                                                |
| --------------------- | -------------------------------------------------------------------------- |
| Implementation Defect | The implementation violates the documented architecture.                   |
| Documentation Defect  | The documentation no longer accurately reflects the accepted architecture. |
| Architectural Defect  | The architecture itself requires revision through a formal ADR.            |

Correct classification prevents implementation work from silently redefining the architecture.

---

## 14.5 Resolution Principle

Whenever practical:

1. Correct the implementation.
2. Correct the documentation if it is inaccurate.
3. Escalate through an ADR only when the architecture itself must change.

This order preserves architectural stability while allowing implementation to evolve.

---

# 15. Governance Principles Summary

The governance model established in this chapter is founded upon the following permanent principles:

* Architecture is intentional.
* Responsibilities have explicit owners.
* Public interfaces are stable contracts.
* Dependencies always point downward.
* Documentation is an architectural asset.
* Architectural evolution is incremental.
* Evidence takes precedence over speculation.
* Significant architectural changes require formal approval.
* Implementation conforms to architecture, not the reverse.

These principles provide the governance framework that enables Local OpenClaw to evolve without sacrificing architectural integrity.

---

## Part C Status

This part establishes the governance mechanisms that preserve architectural consistency over time by defining:

* dependency governance,
* documentation governance,
* the architecture review process,
* compliance verification,
* and the guiding principles of architectural governance.

Together with Parts A and B, these sections define **how the architecture is maintained**, ensuring that future implementation remains aligned with the Software Architecture Specification.


# Document 1 — Project Foundation

## Chapter 4 — Architectural Governance (Part D)

**Local OpenClaw (LOC)**
**Software Architecture Specification (SAS)**
**Document Status:** Authoritative
**Document:** 4 of 5 — Chapter 4 (Part D of IV)

---

# 16. Long-Term Architectural Stewardship

## 16.1 Purpose

The architecture of Local OpenClaw is intended to remain stable throughout the lifetime of the project.

Long-term stewardship ensures that the architecture continues to support new capabilities without sacrificing clarity, maintainability, or subsystem integrity.

Architectural stewardship is a continuous engineering responsibility rather than a one-time design activity.

---

## 16.2 Stewardship Objectives

Long-term architectural stewardship pursues five primary objectives:

* Preserve architectural consistency.
* Protect subsystem ownership.
* Maintain stable public interfaces.
* Encourage incremental evolution.
* Minimize architectural complexity.

Every architectural decision should contribute to one or more of these objectives.

---

## 16.3 Architecture as a Long-Term Asset

The architecture should be regarded as a strategic engineering asset.

Accordingly:

* implementation should evolve within the architecture,
* documentation should evolve with the architecture,
* architecture should evolve only through deliberate governance.

This principle ensures that implementation remains adaptable while architectural knowledge remains durable.

---

# 17. Architectural Maintenance Guidelines

The following guidelines define how the architecture should be maintained throughout future development.

---

## 17.1 Preserve Cohesion

Each subsystem should continue to own a narrowly defined responsibility.

When new functionality is introduced, implementation should strengthen subsystem cohesion rather than expanding responsibilities indiscriminately.

---

## 17.2 Minimize Coupling

New dependencies should be introduced only when they represent genuine architectural relationships.

Implementation convenience should never justify tighter subsystem coupling.

Whenever practical:

* communicate through stable interfaces,
* exchange only required information,
* avoid exposing implementation details.

---

## 17.3 Prefer Extension Over Replacement

Existing architectural structures should be extended before introducing replacements.

Examples include:

* extending an existing provider,
* adding an implementation behind an abstraction,
* expanding subsystem capabilities within established ownership.

Replacement should occur only when an existing architectural assumption has become invalid.

---

## 17.4 Preserve Determinism

Repository understanding should remain deterministic wherever practical.

Equivalent repository states should continue to produce equivalent repository representations.

Deterministic behavior improves:

* reproducibility,
* testing,
* debugging,
* developer trust.

---

## 17.5 Preserve Explicit Ownership

No capability should become jointly owned through gradual implementation changes.

Whenever ownership becomes ambiguous, clarification should occur before implementation continues.

Architectural clarity is preferred over short-term implementation convenience.

---

## 17.6 Maintain Documentation

Architecture documentation should remain synchronized with accepted architectural decisions.

Documentation updates should accompany accepted architectural changes rather than following implementation retroactively.

---

# 18. Governance During Future Development

## 18.1 Evolution Without Drift

Architectural growth should occur without introducing architectural drift.

Architectural drift occurs when implementation gradually diverges from documented architectural intent without explicit approval.

Preventing architectural drift preserves long-term maintainability.

---

## 18.2 Continuous Architectural Validation

Architecture should be validated continuously throughout development.

Typical validation activities include:

* implementation reviews,
* interface reviews,
* dependency verification,
* release validation,
* architectural audits.

These activities complement one another and collectively ensure continued architectural compliance.

---

## 18.3 Engineering Responsibility

Every contributor shares responsibility for preserving architectural integrity.

Responsibilities include:

* respecting subsystem ownership,
* maintaining public interfaces,
* preserving dependency direction,
* documenting architectural changes,
* identifying architectural inconsistencies.

Architectural quality is a collective engineering responsibility.

---

## 18.4 Resolving Architectural Uncertainty

When architectural uncertainty arises during implementation, the preferred order of resolution is:

1. Consult the Software Architecture Specification.
2. Consult accepted ADRs.
3. Verify implementation consistency.
4. Determine whether the issue is architectural or implementation-specific.
5. Initiate architectural review only if existing documentation cannot resolve the uncertainty.

This process minimizes unnecessary architectural change while preserving implementation momentum.

---

# 19. Governance Checklist

The following checklist provides a concise reference for evaluating architectural compliance during development.

Before introducing a significant implementation change, verify:

* [ ] The responsibility belongs to the owning subsystem.
* [ ] No existing subsystem ownership is violated.
* [ ] Dependency direction remains valid.
* [ ] Only stable public interfaces are used.
* [ ] No implementation details leak across subsystem boundaries.
* [ ] Public interfaces remain backward compatible.
* [ ] Existing architectural invariants remain satisfied.
* [ ] Documentation remains consistent with accepted architecture.
* [ ] No accepted ADR is contradicted.
* [ ] No unnecessary abstraction has been introduced.

This checklist is intended as a practical governance aid rather than a replacement for architectural judgment.

---

# 20. Chapter Summary

## 20.1 Purpose of This Chapter

This chapter establishes the governance framework that preserves the long-term integrity of the Local OpenClaw architecture.

While earlier chapters define:

* why the project exists,
* how it is architected,
* and what Version 1 delivers,

this chapter defines how those architectural decisions remain consistent throughout future development.

---

## 20.2 Governance Scope

Architectural governance encompasses:

* architectural decision-making,
* subsystem ownership,
* public interface stability,
* dependency management,
* documentation governance,
* compliance verification,
* long-term architectural stewardship.

Collectively, these mechanisms ensure that Local OpenClaw evolves without sacrificing architectural clarity.

---

## 20.3 Relationship to Implementation

Governance defines the architectural constraints within which implementation occurs.

Implementation remains free to evolve provided that it:

* respects subsystem ownership,
* preserves dependency direction,
* maintains public interfaces,
* complies with accepted ADRs,
* and remains consistent with the Software Architecture Specification.

Governance exists to guide implementation rather than restrict engineering unnecessarily.

---

## 20.4 Long-Term Stability

The governance model established in this chapter is intended to remain valid throughout the lifetime of the project.

Future architectural evolution should occur through:

* deliberate review,
* evidence-based decision making,
* accepted ADRs,
* and corresponding documentation updates.

This approach enables Local OpenClaw to grow incrementally while maintaining architectural integrity.

---

## 20.5 Key Outcomes

Upon completion of this chapter, the Software Architecture Specification now defines:

* the governance process for architectural evolution,
* accepted architectural decisions,
* subsystem ownership,
* frozen public interfaces,
* dependency governance,
* documentation governance,
* compliance verification,
* architectural stewardship,
* and long-term maintenance principles.

These governance mechanisms complement the architectural foundation established in the previous chapters and provide the framework within which all future implementation should occur.

---

# Chapter Completion Status

**Document 1 — Project Foundation**

| Chapter                                  | Status         |
| ---------------------------------------- | -------------- |
| Chapter 1 — Project Definition           | ✅ Complete     |
| Chapter 2 — System Architecture          | ✅ Complete     |
| Chapter 3 — Version 1 Product Scope      | ✅ Complete     |
| **Chapter 4 — Architectural Governance** | ✅ **Complete** |
| Chapter 5 — Reference                    | ⏳ Pending      |

---

# Transition to Chapter 5

With Chapter 4 complete, the Software Architecture Specification now defines:

* **Why** Local OpenClaw exists (Chapter 1),
* **How** it is architected (Chapter 2),
* **What** Version 1 delivers (Chapter 3),
* **How** the architecture is governed and preserved (Chapter 4).

The final chapter, **Reference**, will serve as the authoritative reference section for the Software Architecture Specification. It will consolidate:

* the project glossary,
* the authoritative repository folder structure,
* documentation hierarchy,
* document relationships,
* terminology conventions,
* and guidance for navigating and maintaining the documentation set.

This concluding chapter will complete **Document 1 — Project Foundation** and provide a stable reference for both engineers and future architectural documentation.

---

# Document 1 — Project Foundation

## Chapter 5 — Reference (Part A)

**Local OpenClaw (LOC)**
**Software Architecture Specification (SAS)**
**Document Status:** Authoritative
**Document:** 5 of 5 — Chapter 5 (Part A of III)

---

# Chapter Metadata

| Property          | Value                                                   |
| ----------------- | ------------------------------------------------------- |
| **Document**      | Project Foundation                                      |
| **Chapter**       | Chapter 5 — Reference                                   |
| **Scope**         | Permanent Architectural Reference                       |
| **Stability**     | Frozen (subject only to accepted architectural changes) |
| **Depends On**    | Chapters 1–4                                            |
| **Referenced By** | All project documentation                               |
| **Last Updated**  | Sprint 4 RC-4                                           |

---

# 1. Purpose

## 1.1 Objective

This chapter serves as the permanent reference section of the **Software Architecture Specification (SAS)**.

Unlike the preceding chapters, which define the project's vision, architecture, product scope, and governance, this chapter consolidates the stable reference information required to understand, navigate, and maintain the Local OpenClaw architecture.

Its purpose is to provide a single authoritative reference that remains useful throughout the lifetime of the project.

---

## 1.2 Scope

This chapter documents:

* architectural terminology,
* authoritative project vocabulary,
* repository organization,
* documentation organization,
* naming conventions,
* architectural reference material.

Implementation status, engineering progress, release readiness, and development workflow remain outside the scope of this chapter.

---

## 1.3 Reference Philosophy

Reference documentation should be:

* stable,
* concise,
* implementation-independent,
* internally consistent,
* easily navigable.

Reference material should explain **what architectural concepts mean**, not how they are implemented.

---

# 2. Glossary

The following glossary defines the authoritative architectural terminology used throughout Local OpenClaw.

---

## API

The public communication boundary through which clients interact with Local OpenClaw.

The API exposes application capabilities while delegating all business behavior to the appropriate architectural subsystems.

---

## Architecture Decision Record (ADR)

A formal document describing a significant architectural decision, its rationale, and its long-term consequences.

Accepted ADRs become part of the permanent architecture.

---

## Chunk

A deterministic portion of a repository document produced by the Repository subsystem.

Chunks represent the unit of repository understanding and semantic indexing.

---

## Chunk Boundary

The structural location of a repository chunk within its source document.

Boundaries describe where a chunk begins and ends and may include structural classifications such as module, class, or function.

---

## Embedding

A numerical vector representation of repository content generated by the Indexing subsystem for semantic similarity operations.

Embeddings are internal implementation details of indexing.

---

## Frontend

The user-facing interface responsible for presenting application functionality and managing client-side interaction.

The frontend does not implement domain behavior.

---

## Indexing

The architectural subsystem responsible for transforming repository chunks into searchable semantic representations.

---

## IndexedChunk

An internal indexing model combining repository information with an embedding vector.

IndexedChunk remains internal to the Indexing subsystem.

---

## Local AI

Artificial intelligence capabilities executed entirely on the user's local machine without dependence on cloud-hosted inference.

---

## Memory

The architectural subsystem responsible for persistent contextual knowledge independent of repository structure.

---

## Persistence

The architectural subsystem responsible for durable storage of application information.

Persistence stores data but owns no business logic.

---

## Repository

The canonical representation of the user's software project.

Repository information originates exclusively from the Repository subsystem.

---

## Repository Chunk

A structured representation of repository content prepared for semantic indexing.

Repository chunks are repository-domain models rather than indexing models.

---

## Retrieval

The architectural subsystem responsible for semantic repository search.

Retrieval exposes repository information through retrieval-specific projections.

---

## SearchHit

An internal retrieval projection representing an individual semantic retrieval result.

SearchHit is independent of embedding-aware indexing models.

---

## SearchResponse

The public retrieval response returned by the Retrieval subsystem.

SearchResponse represents the stable retrieval contract exposed to higher architectural layers.

---

## Snapshot

A persistent representation of repository state created to support safe editing and rollback.

Snapshots belong to the Editing subsystem.

---

## Stable Public Interface

A published architectural contract through which subsystems communicate.

Stable interfaces remain compatible unless explicitly modified through an accepted ADR.

---

## Subsystem

A cohesive architectural unit that owns a well-defined responsibility within Local OpenClaw.

Each subsystem owns exactly one primary area of responsibility.

---

## Vector Store

A persistence mechanism capable of storing embedding vectors and performing semantic similarity search.

The VectorStore interface abstracts concrete persistence implementations.

---

# 3. Architectural Terminology

The following terminology conventions apply throughout the project.

---

## 3.1 Repository Terminology

| Preferred Term      | Meaning                                     |
| ------------------- | ------------------------------------------- |
| Repository          | A software project being analyzed.          |
| Repository Entry    | A filesystem entity within a repository.    |
| Repository Document | A loaded textual repository file.           |
| Repository Chunk    | A deterministic unit of repository content. |
| Repository Metadata | Metadata describing repository content.     |

These terms refer exclusively to repository-domain concepts.

---

## 3.2 Indexing Terminology

| Preferred Term | Meaning                                         |
| -------------- | ----------------------------------------------- |
| Embedding      | Numerical semantic representation.              |
| IndexedChunk   | Chunk prepared for vector indexing.             |
| Indexing       | Semantic preparation of repository information. |

Embedding-related terminology remains internal to the Indexing subsystem.

---

## 3.3 Retrieval Terminology

| Preferred Term  | Meaning                        |
| --------------- | ------------------------------ |
| Search Query    | A semantic search request.     |
| Search Hit      | Internal retrieval projection. |
| Search Result   | Public retrieval result.       |
| Search Response | Complete retrieval response.   |

Retrieval terminology should never expose indexing implementation models.

---

## 3.4 Editing Terminology

| Preferred Term | Meaning                                     |
| -------------- | ------------------------------------------- |
| Change         | A repository modification.                  |
| Patch          | A deterministic repository update.          |
| Snapshot       | Recoverable repository state.               |
| Rollback       | Restoration of a previous repository state. |

---

## 3.5 Memory Terminology

| Preferred Term      | Meaning                               |
| ------------------- | ------------------------------------- |
| Fact                | Persistent user or project knowledge. |
| Session             | Conversation-specific working state.  |
| Working Context     | Active contextual information.        |
| Architecture Memory | Long-term architectural knowledge.    |

---

# 4. Naming Conventions

To preserve consistency throughout the codebase and documentation, Local OpenClaw follows a uniform naming strategy.

---

## Classes

Classes represent nouns.

Examples:

* `RepositoryChunk`
* `SearchResponse`
* `RepositoryIndexer`
* `ChromaVectorStore`

---

## Interfaces

Interfaces describe capabilities rather than implementations.

Examples:

* `EmbeddingProvider`
* `VectorStore`
* `StorageProvider`

---

## Services

Services coordinate subsystem behavior.

Service names describe the capability they provide.

Examples:

* `RetrievalService`
* `IndexingService`

---

## Models

Models describe information rather than behavior.

Model names remain technology-independent whenever practical.

---

## Providers

Provider names identify infrastructure capabilities without exposing implementation technologies.

---

## Part A Status

This part establishes the permanent architectural vocabulary of Local OpenClaw by defining:

* the purpose of the reference chapter,
* the authoritative glossary,
* architectural terminology,
* and project-wide naming conventions.

These definitions provide a consistent language for the Software Architecture Specification and all related engineering documentation.

