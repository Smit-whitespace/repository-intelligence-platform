# Document 4 — Continuation Package

## Chapter 1 — Purpose & Usage

**Local OpenClaw (LOC)**
**Project Continuation Specification (PCS)**
**Document Status:** Draft (Pending Final Documentation Freeze)
**Document:** 4 of 5 — Chapter 1 (Part A of V)

---

# Chapter Metadata

| Property          | Value                                                                     |
| ----------------- | ------------------------------------------------------------------------- |
| **Document**      | Continuation Package                                                      |
| **Chapter**       | Chapter 1 — Purpose & Usage                                               |
| **Purpose**       | Define how implementation shall be resumed in future engineering sessions |
| **Scope**         | Sprint 4 continuation and implementation handoff                          |
| **Stability**     | Living Document                                                           |
| **Depends On**    | Documents 0–3                                                             |
| **Referenced By** | Future implementation sessions                                            |
| **Last Updated**  | Sprint 4 RC-4                                                             |

---

# 1. Purpose

## 1.1 Objective

The Continuation Package provides the operational context required to resume development of Local OpenClaw without re-establishing architectural decisions, implementation history, or engineering conventions.

Its primary objective is to ensure that implementation can continue seamlessly across engineering sessions while preserving the integrity of the project's approved architecture and implementation state.

Unlike the preceding documents, which define the project, its implementation, and its release readiness, this document defines **how future work shall proceed**.

---

## 1.2 Scope

This document governs continuation of implementation during Sprint 4.

It defines:

* continuation context,
* implementation assumptions,
* continuation constraints,
* engineering workflow,
* operational roadmap,
* continuation prompt.

It does **not** redefine:

* architecture,
* implementation status,
* release readiness,
* accepted ADRs,
* public interfaces.

Those responsibilities remain with Documents 1–3.

---

# 2. Position Within the Documentation Hierarchy

The Local OpenClaw documentation set is intentionally layered.

Each document owns a distinct responsibility.

| Document                                             | Responsibility                                                       |
| ---------------------------------------------------- | -------------------------------------------------------------------- |
| **Document 0 — Project Manifest**                    | Executive dashboard and navigation                                   |
| **Document 1 — Project Foundation**                  | Permanent Software Architecture Specification                        |
| **Document 2 — Engineering State**                   | Current implementation state                                         |
| **Document 3 — Release State**                       | Release readiness and validation                                     |
| **Document 4 — Continuation Package**                | Operational implementation handoff                                   |
| **Document 5 — Supplementary Engineering Knowledge** | Engineering guidance, conventions, lessons learned, and known issues |

The Continuation Package depends upon the preceding documents and shall never supersede them.

---

# 3. Intended Audience

This document is intended for engineers or AI assistants who are resuming implementation after an interruption.

It assumes no prior knowledge of earlier conversations beyond the approved documentation set.

Readers are expected to rely on the documentation hierarchy rather than attempting to reconstruct project history.

---

# 4. Relationship to the Other Documents

The Continuation Package complements the rest of the documentation suite.

It answers a different question from each preceding document.

| Document                 | Primary Question                            |
| ------------------------ | ------------------------------------------- |
| Project Manifest         | *What is the current state of the project?* |
| Project Foundation       | *What is the system?*                       |
| Engineering State        | *What has been implemented?*                |
| Release State            | *What is required before release?*          |
| **Continuation Package** | **How should implementation continue?**     |

This separation prevents operational guidance from becoming mixed with architecture or implementation specifications.

---

# 5. Continuation Philosophy

Local OpenClaw follows a continuity-first engineering approach.

Implementation continuity is achieved by preserving:

* stable architecture,
* stable subsystem ownership,
* stable public interfaces,
* explicit implementation state,
* documented engineering rules,
* deterministic implementation workflow.

Future implementation should extend the approved system rather than reinterpreting it.

---

# 6. Operational Assumptions

Every continuation session shall assume the following unless explicitly updated by the project owner.

### Architecture

The architecture defined by Document 1 remains authoritative.

No architectural redesign shall occur during Sprint 4.

---

### Engineering State

Document 2 accurately represents the current implementation state.

Implementation shall resume from the current engineering queue rather than revisiting completed work.

---

### Release State

Document 3 defines the current release objectives and remaining release requirements.

Implementation shall remain aligned with those requirements.

---

### Documentation

The documentation suite represents the authoritative project knowledge.

Implementation should reference the documentation rather than reconstructing context from prior discussions.

---

# 7. Scope of Continuation

The Continuation Package governs only the continuation of the current implementation effort.

It does not prescribe:

* future product planning,
* post-Version 1 roadmap,
* architectural redesign,
* research activities,
* experimental implementation.

Those activities require separate planning outside the scope of this document.

---

# 8. Documentation Usage

The recommended reading order for a new engineer or AI assistant is:

1. **Document 0 — Project Manifest**
   Obtain a high-level understanding of the project's current state.

2. **Document 1 — Project Foundation**
   Understand the permanent architecture and subsystem boundaries.

3. **Document 2 — Engineering State**
   Review current implementation progress.

4. **Document 3 — Release State**
   Understand release requirements and validation obligations.

5. **Document 4 — Continuation Package**
   Resume implementation using the operational guidance contained herein.

6. **Document 5 — Supplementary Engineering Knowledge**
   Consult implementation conventions, lessons learned, and known issues as needed.

Following this sequence minimizes context reconstruction and preserves consistency across engineering sessions.

---

# 9. Chapter Summary

This chapter establishes the purpose, scope, and usage of the Continuation Package.

It defines:

* why the document exists,
* its place within the documentation hierarchy,
* its intended audience,
* its relationship to the other project documents,
* the operational assumptions under which implementation shall continue,
* and the recommended process for using the documentation suite to resume development.

These foundations enable subsequent chapters to focus exclusively on the practical mechanics of continuing implementation.

---


# Document 4 — Continuation Package

## Chapter 2 — Current Continuation State

**Local OpenClaw (LOC)**
**Project Continuation Specification (PCS)**
**Document Status:** Draft (Pending Final Documentation Freeze)
**Document:** 4 of 5 — Chapter 2 (Part B of V)

---

# Chapter Metadata

| Property          | Value                                                                          |
| ----------------- | ------------------------------------------------------------------------------ |
| **Document**      | Continuation Package                                                           |
| **Chapter**       | Chapter 2 — Current Continuation State                                         |
| **Purpose**       | Establish the exact engineering context from which implementation shall resume |
| **Scope**         | Sprint 4 RC-4 continuation baseline                                            |
| **Stability**     | Living Document                                                                |
| **Depends On**    | Documents 0–3                                                                  |
| **Referenced By** | Chapters 3–5                                                                   |
| **Last Updated**  | Sprint 4 RC-4                                                                  |

---

# 1. Purpose

## 1.1 Objective

This chapter defines the precise continuation context for Local OpenClaw.

Its objective is to eliminate ambiguity when implementation resumes after an interruption.

Every future implementation session should be able to determine:

* the current development phase,
* the active sprint,
* the current release candidate,
* the next implementation task,
* the remaining work,
* the current validation state,

without consulting historical conversations.

---

# 2. Current Project State

## Project Snapshot

| Property             | Current State                         |
| -------------------- | ------------------------------------- |
| Project              | Local OpenClaw                        |
| Version              | Version 1                             |
| Development Phase    | Core Implementation & Stabilization   |
| Current Sprint       | Sprint 4                              |
| Release Candidate    | RC-4                                  |
| Architecture Status  | Frozen                                |
| Engineering Status   | Implementation Substantially Complete |
| Release Status       | Stabilization In Progress             |
| Documentation Status | In Progress                           |

---

## Current Engineering Objective

The current engineering objective is to complete Sprint 4 by:

* finishing the remaining approved implementation,
* completing the remaining behavioral test suites,
* executing repository-wide validation,
* stabilizing verified defects,
* completing the documentation suite,
* satisfying all release gates,
* formally freezing Sprint 4.

No architectural expansion is planned during the current sprint.

---

# 3. Current Working Context

## Active Development Focus

The project has transitioned from primary implementation to stabilization.

Current engineering work is centered on:

1. remaining behavioral tests,
2. repository-wide validation,
3. stabilization,
4. release preparation.

The implementation phase is therefore validation-driven rather than feature-driven.

---

## Current Working File

At the time this chapter was generated:

**Primary engineering activity:**

Completion of the project documentation suite.

**Next production implementation file:**

```text
backend/tests/indexing/test_chroma_store.py
```

This remains the highest-priority implementation task immediately after documentation is completed.

Implementation shall continue with this file unless superseded by verified validation failures.

---

# 4. Immediate Implementation Queue

The approved implementation order is:

| Order | Task                                                         |
| ----- | ------------------------------------------------------------ |
| 1     | Implement `backend/tests/indexing/test_chroma_store.py`      |
| 2     | Implement `backend/tests/indexing/test_retrieval_service.py` |
| 3     | Execute Ruff                                                 |
| 4     | Execute MyPy                                                 |
| 5     | Execute Pytest                                               |
| 6     | Stabilize verified defects                                   |
| 7     | Validate metadata round-trip behavior                        |
| 8     | Complete release documentation                               |
| 9     | Freeze Sprint 4                                              |

Implementation should proceed sequentially unless a verified defect requires a temporary deviation.

---

# 5. Current Validation State

Repository-wide validation has not yet been executed.

Current status:

| Activity                            | Status                 |
| ----------------------------------- | ---------------------- |
| Remaining Production Implementation | Substantially Complete |
| Remaining Behavioral Tests          | Pending                |
| Ruff                                | Pending                |
| MyPy                                | Pending                |
| Pytest                              | Pending                |
| Runtime Validation                  | Pending                |
| Metadata Round-Trip Validation      | Pending                |

Until these activities complete successfully, implementation remains in the stabilization phase.

---

# 6. Current Known Blocking Items

The following items currently prevent Sprint 4 from being frozen.

## Mandatory Remaining Work

* Complete `test_chroma_store.py`.
* Complete `test_retrieval_service.py`.
* Execute repository-wide validation.
* Resolve verified implementation defects.
* Resolve verified test defects.
* Validate metadata round-trip behavior.
* Complete Documents 4 and 5.
* Perform final documentation consistency review.
* Generate release artifacts.
* Formally freeze Sprint 4.

No additional blockers are currently documented.

---

# 7. Current Engineering Assumptions

The following assumptions remain valid until explicitly superseded.

### Architecture

Architecture is complete and frozen.

No architectural redesign shall occur during Sprint 4.

---

### Public Interfaces

All accepted public interfaces remain frozen.

Any change requires evidence that a verified implementation issue cannot be resolved within the existing interface.

---

### Subsystem Ownership

Subsystem ownership defined by the Software Architecture Specification remains authoritative.

Implementation shall preserve these boundaries.

---

### Engineering State

Document 2 accurately represents the current implementation state.

Implementation shall continue from that baseline.

---

### Release State

Document 3 defines the current release requirements.

Completion of those requirements remains mandatory before Sprint 4 can be frozen.

---

# 8. Continuation Starting Point

When implementation resumes, the following sequence shall be followed:

1. Review the current working file.
2. Verify consistency with Documents 1–3.
3. Audit the target implementation.
4. Apply the minimal required implementation.
5. Review the implementation.
6. Validate the implementation.
7. Stabilize verified defects if necessary.
8. Return to the implementation queue.

This process preserves implementation continuity while minimizing unnecessary context reconstruction.

---

# 9. Suspension & Resumption Policy

Implementation sessions may end at any point.

When resuming:

* do not revisit completed implementation,
* do not reopen accepted architectural decisions,
* do not reinterpret subsystem ownership,
* resume from the highest-priority unfinished task documented in this chapter.

The documentation suite shall serve as the authoritative project memory rather than previous conversations.

---

# 10. Chapter Summary

This chapter establishes the exact continuation state for Sprint 4.

It records:

* the current project snapshot,
* the active engineering objective,
* the current working file,
* the approved implementation queue,
* the current validation state,
* the remaining release blockers,
* the engineering assumptions,
* and the required starting point for every future implementation session.

Together with the following chapters, it enables any engineer or AI assistant to resume development immediately while preserving the approved architecture, implementation state, and release objectives.

---


# Document 4 — Continuation Package

## Chapter 3 — Continuation Rules

**Local OpenClaw (LOC)**
**Project Continuation Specification (PCS)**
**Document Status:** Draft (Pending Final Documentation Freeze)
**Document:** 4 of 5 — Chapter 3 (Part C of V)

---

# Chapter Metadata

| Property          | Value                                                               |
| ----------------- | ------------------------------------------------------------------- |
| **Document**      | Continuation Package                                                |
| **Chapter**       | Chapter 3 — Continuation Rules                                      |
| **Purpose**       | Define the mandatory rules governing continuation of implementation |
| **Scope**         | Sprint 4 RC-4 continuation workflow                                 |
| **Stability**     | Living Document                                                     |
| **Depends On**    | Documents 0–3                                                       |
| **Referenced By** | Chapters 4–5                                                        |
| **Last Updated**  | Sprint 4 RC-4                                                       |

---

# 1. Purpose

## 1.1 Objective

This chapter establishes the mandatory engineering rules that govern every future implementation session.

These rules ensure implementation continues consistently, predictably, and without architectural drift, regardless of whether work is performed by a human engineer or an AI assistant.

The rules defined here are operational constraints. They do not redefine the project's architecture, implementation state, or release requirements.

---

# 2. Governing Principles

Every continuation session shall begin with the following assumptions:

* The Software Architecture Specification (Document 1) is authoritative.
* The Engineering State (Document 2) reflects the current implementation baseline.
* The Release State (Document 3) defines the current release objectives.
* This Continuation Package defines how implementation proceeds.

No document supersedes another outside its defined responsibility.

---

# 3. Architecture Preservation Rules

During Sprint 4:

* The architecture shall be treated as frozen.
* Accepted ADRs shall remain authoritative.
* Subsystem ownership shall not be modified.
* Public interfaces shall not be redesigned.
* Dependency direction shall remain consistent with Document 1.
* Architectural invariants shall be preserved.

Architecture discussions are closed unless explicitly reopened by the project owner or required to resolve a verified conflict that cannot be addressed within the existing architecture.

---

# 4. Implementation Rules

Implementation shall proceed incrementally and with a clearly defined objective.

Every implementation task shall:

1. Begin with an audit of the target file.
2. Verify consistency with the Software Architecture Specification.
3. Identify the minimum required change.
4. Implement only the approved scope.
5. Review the implementation.
6. Validate the result.
7. Return the file to a stable state before proceeding.

Unrelated refactoring shall not be combined with functional implementation.

---

# 5. File-Level Workflow

Implementation shall progress one file at a time.

For each file:

1. Identify the engineering objective.
2. Review the existing implementation.
3. Confirm consistency with frozen interfaces.
4. Apply the minimum required change.
5. Complete the file.
6. Validate the file.
7. Mark the file with its current engineering status.
8. Proceed to the next item in the implementation queue.

Partially completed implementation should not be abandoned in favor of unrelated work.

---

# 6. Scope Control Rules

During Sprint 4, implementation shall remain within the approved scope.

The following activities are prohibited unless explicitly authorized:

* introducing new architectural patterns,
* expanding Version 1 scope,
* redesigning subsystem boundaries,
* introducing speculative abstractions,
* modifying unrelated files,
* implementing deferred capabilities,
* optimizing without evidence of necessity.

Engineering effort shall remain focused on approved implementation and verified stabilization work.

---

# 7. Validation Rules

Validation is mandatory before implementation is considered complete.

Repository-wide validation shall include:

* Ruff,
* MyPy,
* Pytest,
* runtime verification where required.

Validation shall be executed only after the remaining approved implementation has been completed.

Failures discovered during validation shall be classified before corrective action begins.

---

# 8. Defect Resolution Policy

Only verified defects shall result in implementation changes.

Each issue shall be classified as one of:

* implementation defect,
* test defect,
* documentation defect,
* configuration defect.

Corrective work shall be:

* minimal,
* localized,
* evidence-based,
* consistent with the frozen architecture.

Implementation shall not be modified in anticipation of hypothetical defects.

---

# 9. Escalation Rule

Implementation issues shall be resolved within the existing architecture whenever possible.

If a verified issue cannot be resolved without violating:

* an accepted ADR,
* a frozen public interface,
* a subsystem boundary,
* or an architectural invariant,

implementation shall stop and an architecture review shall be explicitly requested.

No architectural redesign shall occur implicitly during implementation.

---

# 10. Documentation Synchronization

Implementation and documentation shall remain synchronized.

When implementation changes affect documented engineering state or release state:

* the appropriate document shall be updated,
* cross-document consistency shall be preserved,
* architecture documentation shall remain unchanged unless a new ADR has been accepted.

Documentation shall reflect verified implementation rather than planned implementation.

---

# 11. Session Completion Rules

An implementation session should conclude only after:

* the current file reaches a stable state,
* the engineering objective has been completed or a verified blocker has been identified,
* documentation has been updated if required,
* the next implementation task is clearly identified.

This minimizes ambiguity when work resumes.

---

# 12. Session Resumption Rules

Every future implementation session shall begin by:

1. Reviewing Document 0 for the current project snapshot.
2. Reviewing Documents 1–3 as required.
3. Reviewing this Continuation Package.
4. Confirming the current working file.
5. Verifying the implementation queue.
6. Resuming work from the highest-priority unfinished task.

Historical conversations shall not be treated as authoritative project documentation.

---

# 13. Engineering Constraints

The following constraints remain mandatory throughout Sprint 4:

* Preserve architectural stability.
* Preserve subsystem ownership.
* Preserve public interfaces.
* Prefer correctness over implementation speed.
* Prefer clarity over cleverness.
* Prefer explicit behavior over implicit behavior.
* Prefer incremental stabilization over broad refactoring.
* Modify only what is necessary to achieve the approved engineering objective.

These constraints ensure that Sprint 4 concludes with a stable and maintainable codebase.

---

# 14. Chapter Summary

This chapter establishes the operational rules governing continuation of Local OpenClaw implementation.

It defines:

* architecture preservation rules,
* implementation workflow,
* file-level execution,
* scope control,
* validation requirements,
* defect resolution policy,
* escalation procedures,
* documentation synchronization,
* session completion,
* session resumption,
* and engineering constraints.

These rules provide a consistent operational framework for every future implementation session while preserving the integrity of the Software Architecture Specification and the current Engineering and Release States.

---


# Document 4 — Continuation Package

## Chapter 4 — Immediate Implementation Roadmap

**Local OpenClaw (LOC)**
**Project Continuation Specification (PCS)**
**Document Status:** Draft (Pending Final Documentation Freeze)
**Document:** 4 of 5 — Chapter 4 (Part D of V)

---

# Chapter Metadata

| Property          | Value                                                                        |
| ----------------- | ---------------------------------------------------------------------------- |
| **Document**      | Continuation Package                                                         |
| **Chapter**       | Chapter 4 — Immediate Implementation Roadmap                                 |
| **Purpose**       | Define the operational implementation sequence required to complete Sprint 4 |
| **Scope**         | Remaining implementation and stabilization work                              |
| **Stability**     | Living Document                                                              |
| **Depends On**    | Documents 1–3 and Chapter 3 of this document                                 |
| **Referenced By** | Chapter 5 — Canonical Continuation Prompt                                    |
| **Last Updated**  | Sprint 4 RC-4                                                                |

---

# 1. Purpose

## 1.1 Objective

This chapter translates the Engineering State and Release State into a practical execution roadmap.

Its purpose is to answer one operational question:

> **"What should be done next, in what order, and under what conditions?"**

Unlike Document 2, which records engineering progress, this roadmap is action-oriented. It is intended to guide implementation from the current state to Sprint 4 completion.

---

# 2. Current Starting Point

At the time of this document revision:

* Architecture is frozen.
* Production implementation is substantially complete.
* Core indexing and retrieval implementation have been completed and reviewed.
* Remaining work is concentrated in behavioral testing, validation, stabilization, and release preparation.

The next implementation activity begins with the highest-priority unfinished item in the approved engineering queue.

---

# 3. Phase-Based Execution Roadmap

Sprint 4 completion is divided into six sequential phases.

Each phase has a clearly defined objective, dependencies, and completion criteria.

---

## Phase 1 — Remaining Behavioral Test Implementation

### Objective

Complete the remaining approved behavioral test suites for the retrieval subsystem.

### Primary Files

```text
backend/tests/indexing/test_chroma_store.py
backend/tests/indexing/test_retrieval_service.py
```

### Required Outcome

* Behavioral coverage implemented.
* Tests aligned with frozen public interfaces.
* No production implementation changes unless a verified defect is discovered.

### Exit Criteria

Both test suites are complete and ready for repository-wide validation.

---

## Phase 2 — Repository-Wide Validation

### Objective

Validate the repository against all approved engineering quality gates.

### Validation Sequence

1. Ruff
2. MyPy
3. Pytest
4. Runtime validation

Validation shall proceed sequentially.

Failures shall halt progression until classified.

### Exit Criteria

All validation activities have completed successfully or produced verified defects for stabilization.

---

## Phase 3 — Stabilization

### Objective

Resolve issues identified during validation.

### Permitted Work

* Correct implementation defects.
* Correct test defects.
* Correct documentation defects.
* Correct configuration defects.

No speculative refactoring shall occur during this phase.

### Exit Criteria

Repository validation succeeds without unresolved verified defects.

---

## Phase 4 — Metadata Round-Trip Verification

### Objective

Verify runtime reconstruction of repository metadata through the Chroma adapter.

### Required Activities

* Execute runtime validation.
* Confirm metadata reconstruction behavior.
* Complete the deferred repository model reconstruction test if runtime behavior matches the approved implementation.
* Otherwise classify the discrepancy and stabilize accordingly.

### Exit Criteria

Metadata behavior is verified and documented.

---

## Phase 5 — Documentation Finalization

### Objective

Complete and normalize the project documentation suite.

### Activities

* Complete Documents 4 and 5.
* Perform cross-document consistency review.
* Verify document references.
* Confirm terminology consistency.
* Confirm implementation status consistency.

### Exit Criteria

The documentation suite is internally consistent and ready for freeze.

---

## Phase 6 — Sprint Freeze

### Objective

Formally conclude Sprint 4.

### Activities

* Generate release documentation.
* Generate Sprint checkpoint.
* Confirm all release gates have passed.
* Freeze the documentation suite.
* Freeze Sprint 4.

### Exit Criteria

Sprint 4 is formally complete.

---

# 4. Immediate Engineering Queue

The approved implementation queue is reproduced here as the operational execution list.

| Order | Activity                                                     | Category           |
| ----: | ------------------------------------------------------------ | ------------------ |
|     1 | Implement `backend/tests/indexing/test_chroma_store.py`      | Testing            |
|     2 | Implement `backend/tests/indexing/test_retrieval_service.py` | Testing            |
|     3 | Execute Ruff                                                 | Validation         |
|     4 | Execute MyPy                                                 | Validation         |
|     5 | Execute Pytest                                               | Validation         |
|     6 | Stabilize verified defects                                   | Stabilization      |
|     7 | Validate metadata round-trip behavior                        | Runtime Validation |
|     8 | Complete Documents 4 and 5                                   | Documentation      |
|     9 | Perform documentation consistency review                     | Documentation      |
|    10 | Generate release artifacts                                   | Release            |
|    11 | Freeze Sprint 4                                              | Release            |

Tasks shall normally be executed in order unless a verified defect requires temporary reprioritization.

---

# 5. Decision Points

Implementation proceeds through several mandatory decision points.

## Decision Point 1 — After Behavioral Tests

Question:

> Are all approved behavioral tests implemented?

If **No**, continue implementation.

If **Yes**, proceed to repository-wide validation.

---

## Decision Point 2 — After Validation

Question:

> Did validation discover verified defects?

If **Yes**, enter stabilization.

If **No**, proceed to metadata verification.

---

## Decision Point 3 — After Metadata Verification

Question:

> Does runtime behavior match the approved implementation?

If **Yes**, complete the deferred metadata round-trip behavioral test.

If **No**, classify the discrepancy and stabilize the affected artifact.

---

## Decision Point 4 — Before Sprint Freeze

Question:

> Have all release gates been satisfied?

If **No**, continue remaining work.

If **Yes**, prepare Sprint freeze.

---

# 6. Success Metrics

Progress toward Sprint 4 completion shall be measured using the following indicators.

| Metric                              | Target   |
| ----------------------------------- | -------- |
| Remaining production implementation | Complete |
| Remaining behavioral tests          | Complete |
| Ruff                                | Passing  |
| MyPy                                | Passing  |
| Pytest                              | Passing  |
| Metadata validation                 | Verified |
| Documentation                       | Complete |
| Release gates                       | Passed   |
| Sprint status                       | Frozen   |

These metrics provide objective evidence of completion.

---

# 7. Stopping Conditions

Implementation shall pause only under one of the following conditions:

* The current engineering objective has been completed.
* A verified blocker prevents further progress.
* An issue requires an explicit architecture review because it cannot be resolved within the frozen architecture.
* Sprint 4 has been formally frozen.

Implementation should not stop because of uncertainty that can be resolved through validation.

---

# 8. Roadmap Summary

The remainder of Sprint 4 is intentionally linear.

The overall execution path is:

```text
Remaining Tests
        │
        ▼
Repository Validation
        │
        ▼
Stabilization
        │
        ▼
Metadata Verification
        │
        ▼
Documentation Finalization
        │
        ▼
Sprint Freeze
```

This roadmap minimizes context switching and preserves the stability of the implementation while progressing toward release.

---

# Chapter Summary

This chapter establishes the operational execution roadmap for completing Sprint 4.

It defines:

* the current starting point,
* the implementation phases,
* the immediate engineering queue,
* mandatory decision points,
* success metrics,
* stopping conditions,
* and the overall execution path.

Together with the continuation rules defined in the previous chapter, this roadmap provides a clear, deterministic process for completing the remaining work without revisiting architectural decisions or deviating from the approved implementation plan.

---


# Document 4 — Continuation Package

## Chapter 5 — Canonical Continuation Prompt

**Local OpenClaw (LOC)**
**Project Continuation Specification (PCS)**
**Document Status:** Draft (Pending Final Documentation Freeze)
**Document:** 4 of 5 — Chapter 5

---

# Chapter Metadata

| Property          | Value                                                                             |
| ----------------- | --------------------------------------------------------------------------------- |
| **Document**      | Continuation Package                                                              |
| **Chapter**       | Chapter 5 — Canonical Continuation Prompt                                         |
| **Purpose**       | Define the authoritative initialization prompt for future implementation sessions |
| **Scope**         | Sprint 4 continuation                                                             |
| **Stability**     | Living Document                                                                   |
| **Depends On**    | Documents 0–4                                                                     |
| **Referenced By** | Future implementation sessions                                                    |
| **Last Updated**  | Sprint 4 RC-4                                                                     |

---

# 1. Purpose

This chapter provides the canonical initialization prompt for any future implementation session involving Local OpenClaw.

Unlike the preceding chapters, which describe the continuation context and operational rules, this prompt is intended to be copied into a new engineering session to establish the correct project context immediately.

Its purpose is to eliminate the need to reconstruct project state from previous conversations while ensuring that implementation remains consistent with the approved documentation.

---

# 2. Canonical Continuation Prompt

```text
You are joining the Local OpenClaw (LOC) project as a Senior Software Engineer.

Your responsibility is to continue implementation of an existing, architecturally frozen codebase.

The project documentation is authoritative and must be treated as the single source of truth.

Documentation hierarchy:

1. Document 0 — Project Manifest
   Executive dashboard and navigation.

2. Document 1 — Project Foundation
   Permanent Software Architecture Specification.
   Defines subsystem ownership, accepted ADRs, dependency rules, public interfaces, architectural invariants, and Version 1 scope.

3. Document 2 — Engineering State
   Current implementation state.
   Defines completed implementation, remaining implementation, engineering inventory, implementation roadmap, and validation readiness.

4. Document 3 — Release State
   Current release readiness.
   Defines release gates, validation requirements, accepted technical debt, deferred work, Definition of Done, and release completion criteria.

5. Document 4 — Continuation Package
   Operational implementation guidance.
   Defines continuation rules, implementation workflow, current working context, and this initialization prompt.

6. Document 5 — Supplementary Engineering Knowledge
   Engineering conventions, lessons learned, coding conventions, known issues, implementation guidance, and practical engineering knowledge.

Treat these documents collectively as the authoritative project documentation.

Do not reconstruct project history from previous conversations.

------------------------------------------------------------

Project Status

Project:
Local OpenClaw (LOC)

Version:
Version 1

Current Sprint:
Sprint 4

Current Release Candidate:
RC-4

Current Phase:
Implementation Stabilization

Architecture Status:
Frozen

Engineering Status:
Implementation Substantially Complete

Release Status:
Stabilization In Progress

------------------------------------------------------------

Architecture Constraints

The Software Architecture Specification is frozen.

Accepted ADRs remain authoritative.

Frozen public interfaces shall not be modified unless a verified implementation issue cannot be resolved within the existing interface.

Subsystem ownership shall remain unchanged.

Dependency direction shall remain unchanged.

Architectural invariants shall remain unchanged.

Do not reopen architecture discussions unless explicitly requested by the project owner or required because a verified implementation issue cannot be resolved within the accepted architecture.

------------------------------------------------------------

Implementation Rules

Work on one file at a time.

Before modifying any file:

1. Audit the existing implementation.
2. Verify consistency with the Software Architecture Specification.
3. Identify the minimum required change.
4. Preserve existing public interfaces.
5. Preserve subsystem ownership.
6. Preserve dependency direction.

Do not perform speculative refactoring.

Do not introduce new abstractions without explicit approval.

Do not modify unrelated files.

Do not broaden implementation scope beyond the approved engineering objective.

------------------------------------------------------------

Current Implementation State

Core implementation is substantially complete.

Current engineering focus is:

- remaining behavioral tests,
- repository-wide validation,
- stabilization,
- release preparation.

The next implementation task is:

backend/tests/indexing/test_chroma_store.py

After completion, continue with:

backend/tests/indexing/test_retrieval_service.py

Then proceed to:

- Ruff
- MyPy
- Pytest
- Stabilization of verified defects
- Metadata round-trip validation
- Documentation finalization
- Sprint freeze

------------------------------------------------------------

Validation Rules

Repository-wide validation shall be executed in the following order:

1. Ruff
2. MyPy
3. Pytest
4. Runtime validation

Failures shall be classified before corrective work begins.

Only verified defects shall result in implementation changes.

------------------------------------------------------------

Defect Classification

Every issue shall be classified as one of:

- Implementation defect
- Test defect
- Documentation defect
- Configuration defect

Corrective work shall be minimal, localized, and evidence-based.

------------------------------------------------------------

Escalation Rule

If a verified implementation issue cannot be resolved without violating:

- an accepted ADR,
- a frozen public interface,
- a subsystem boundary,
- or an architectural invariant,

stop implementation and explicitly request an architecture review.

Do not redesign the architecture implicitly.

------------------------------------------------------------

Working Style

Act as a Senior Software Engineer implementing a frozen design.

Do not act as an architect unless explicitly instructed.

Prefer correctness over cleverness.

Prefer explicit behavior over implicit behavior.

Prefer maintainability over unnecessary abstraction.

Preserve subsystem boundaries.

Maintain documentation consistency when implementation changes affect documented engineering or release state.

------------------------------------------------------------

Stopping Conditions

Pause implementation only when:

- the current file has reached a stable state,
- a verified blocker has been identified,
- an architecture review is required,
- or Sprint 4 has been formally frozen.

Otherwise continue sequentially through the approved implementation queue.

Begin by auditing the current working file, then continue implementation according to the Engineering State and Release State documents.
```

---

# 3. Prompt Usage

The canonical continuation prompt should be used whenever:

* implementation resumes in a new engineering session,
* a new engineer joins the project,
* a new AI assistant is tasked with continuing implementation,
* long-term project continuity is required.

The prompt assumes that the complete documentation suite is available.

If any referenced document has changed since the previous implementation session, the updated documentation shall take precedence.

---

# 4. Maintenance Rules

This continuation prompt should be updated only when one or more of the following occur:

* the current implementation phase changes,
* the implementation queue changes,
* the release candidate changes,
* the documentation hierarchy changes,
* the engineering workflow changes,
* Sprint 4 is formally frozen.

Architectural changes shall continue to be governed exclusively through accepted ADRs and reflected first in **Document 1 — Project Foundation**.

---

# 5. Chapter Summary

This chapter defines the canonical continuation prompt for Local OpenClaw.

The prompt establishes:

* project identity,
* documentation hierarchy,
* current implementation state,
* frozen architectural constraints,
* implementation workflow,
* validation sequence,
* defect resolution policy,
* escalation rules,
* working style,
* and stopping conditions.

It is intended to provide a complete initialization context for any future engineering session without requiring reconstruction of previous conversations.

---

# Document 4 Completion Summary

With the completion of Chapter 5, **Document 4 — Continuation Package** is complete.

It provides a comprehensive operational handoff consisting of:

### Chapter 1 — Purpose & Usage

* Purpose and scope
* Documentation hierarchy
* Operational assumptions
* Intended audience

### Chapter 2 — Current Continuation State

* Project snapshot
* Current implementation focus
* Working file
* Implementation queue
* Validation state

### Chapter 3 — Continuation Rules

* Architecture preservation
* Implementation workflow
* Scope control
* Validation rules
* Escalation policy
* Engineering constraints

### Chapter 4 — Immediate Implementation Roadmap

* Remaining implementation phases
* Decision points
* Success metrics
* Stopping conditions
* Sprint completion roadmap

### Chapter 5 — Canonical Continuation Prompt

* Complete project initialization prompt
* Operational guidance
* Usage and maintenance rules

---

