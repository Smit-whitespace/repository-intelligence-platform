# Document 5 — Supplementary Engineering Knowledge

## Chapter 1 — Current Engineering Knowledge

**Local OpenClaw (LOC)**
**Engineering Knowledge Reference (EKR)**
**Document Status:** Draft (Pending Final Documentation Freeze)
**Document:** 5 of 5 — Chapter 1 (Part A of IV)

---

# Chapter Metadata

| Property          | Value                                                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Document**      | Supplementary Engineering Knowledge                                                                                      |
| **Chapter**       | Chapter 1 — Current Engineering Knowledge                                                                                |
| **Purpose**       | Capture verified engineering knowledge and current validation unknowns that complement the primary project documentation |
| **Scope**         | Sprint 4 RC-4                                                                                                            |
| **Stability**     | Living Document                                                                                                          |
| **Depends On**    | Documents 0–4                                                                                                            |
| **Referenced By** | Future engineering and release stabilization activities                                                                  |
| **Last Updated**  | Sprint 4 RC-4                                                                                                            |

---

# 1. Purpose

## 1.1 Objective

This chapter records engineering knowledge that is valuable for implementation and stabilization but does not belong in the Software Architecture Specification, Engineering State, Release State, or Continuation Package.

Its purpose is to preserve engineering context that would otherwise be lost between implementation sessions while avoiding duplication of the primary documentation.

This chapter intentionally distinguishes:

* verified engineering facts,
* engineering assumptions awaiting validation,
* known uncertainties,
* implementation observations.

It does **not** redefine architecture, implementation status, or release readiness.

---

## 1.2 Scope

This chapter documents:

* verified engineering observations,
* known implementation uncertainties,
* runtime validation unknowns,
* current engineering assumptions,
* evidence-based implementation concerns.

Only information useful for engineering decisions should be recorded here.

---

# 2. Verified Engineering Knowledge

The following statements have been verified through architecture review and implementation review.

## 2.1 Architecture Stability

The Software Architecture Specification is complete for Version 1.

Subsystem ownership, dependency direction, accepted ADRs, architectural invariants, and public interfaces are considered stable for Sprint 4.

Implementation shall preserve these foundations.

---

## 2.2 Implementation Strategy

Sprint 4 follows a stabilization-first approach.

Engineering effort is focused on:

* completing remaining approved implementation,
* behavioral verification,
* repository-wide validation,
* defect stabilization,
* release preparation.

No architectural expansion is planned.

---

## 2.3 Public Interface Stability

The public contracts reviewed during Sprint 4 are considered stable.

Future implementation should prefer adapting internal implementation rather than modifying public interfaces.

Interface changes should occur only when required to resolve a verified incompatibility that cannot be addressed within the existing design.

---

## 2.4 Evidence-Based Engineering

Engineering decisions throughout Sprint 4 are based on implementation evidence rather than assumptions.

Compiler diagnostics, type-checking results, automated tests, and runtime behavior remain the authoritative sources for determining whether implementation changes are required.

---

# 3. Known Current Issues

At the time of writing, no verified production implementation defects have been identified.

The following items remain engineering activities rather than confirmed defects.

---

## Issue 1 — Repository-Wide Validation Pending

### Description

Repository-wide validation has not yet been executed.

Implementation correctness has therefore been established through review rather than complete repository verification.

### Expected Detection

* Ruff
* MyPy
* Pytest

### Severity

**Medium**

### Recommended Resolution

Execute the planned validation sequence and classify any resulting failures before modifying implementation.

---

## Issue 2 — Runtime Metadata Verification Pending

### Description

The runtime behavior of metadata persistence and reconstruction through the Chroma adapter has not yet been confirmed by execution.

### Expected Detection

* Runtime validation
* Pytest

### Severity

**Medium**

### Recommended Resolution

Validate runtime behavior before adding the deferred metadata round-trip behavioral test.

---

## Issue 3 — Remaining Behavioral Test Coverage

### Description

Two approved behavioral test suites remain to be implemented.

This is planned engineering work rather than an implementation defect.

### Expected Detection

Engineering review.

### Severity

**Low**

### Recommended Resolution

Complete the approved behavioral tests before repository-wide validation.

---

# 4. Engineering Assumptions Awaiting Validation

The following assumptions currently guide implementation but shall remain subject to repository-wide validation.

---

## Assumption A — Static Analysis

The implementation is expected to satisfy repository-wide Ruff validation.

This remains an assumption until validation has been executed.

---

## Assumption B — Type Correctness

The implementation is expected to satisfy repository-wide MyPy validation.

Any type inconsistencies discovered shall be resolved through normal stabilization procedures.

---

## Assumption C — Behavioral Correctness

The implemented subsystem interactions are expected to satisfy the approved behavioral test suites.

Repository-wide Pytest execution remains the authoritative verification mechanism.

---

## Assumption D — Adapter Runtime Behavior

The Chroma adapter is expected to reconstruct persisted metadata consistently with the reviewed implementation.

This assumption shall be confirmed through runtime validation before being treated as verified engineering knowledge.

---

# 5. Current Validation Unknowns

The following questions cannot be answered conclusively without executing the repository.

These items are **unknowns**, not implementation defects.

| Area                                   | Current Status | Verification Method |
| -------------------------------------- | -------------- | ------------------- |
| Ruff compliance                        | Unknown        | Ruff                |
| MyPy compliance                        | Unknown        | MyPy                |
| Repository-wide behavioral correctness | Unknown        | Pytest              |
| Runtime metadata reconstruction        | Unknown        | Runtime validation  |
| Repository-wide interface consistency  | Unknown        | Validation suite    |

These unknowns should transition into verified knowledge as Sprint 4 stabilization progresses.

---

# 6. Engineering Observations

The following observations have influenced the implementation process and should remain visible throughout Sprint 4.

---

## Observation 1

Clear subsystem ownership significantly reduced implementation complexity by limiting the scope of individual engineering changes.

---

## Observation 2

Freezing public interfaces before completing the remaining implementation simplified stabilization and reduced unnecessary redesign.

---

## Observation 3

Separating architecture documentation from engineering and release documentation improved maintainability by ensuring each document owns a single responsibility.

---

## Observation 4

Behavioral testing based on public contracts provides a more maintainable validation strategy than testing implementation details.

---

## Observation 5

Incremental implementation combined with structured review reduced the likelihood of architectural drift during Sprint 4.

---

# 7. Knowledge Maintenance Rules

This chapter should be updated only when one of the following occurs:

* a current unknown becomes verified,
* a verified engineering issue is discovered,
* an engineering assumption is invalidated,
* runtime validation establishes new engineering knowledge,
* completed stabilization changes the project's engineering understanding.

This chapter shall not duplicate implementation state or release status maintained by other documents.

---

# 8. Chapter Summary

This chapter captures the engineering knowledge that complements the primary project documentation.

It records:

* verified engineering knowledge,
* known current issues,
* engineering assumptions awaiting validation,
* runtime validation unknowns,
* engineering observations,
* and maintenance rules for this knowledge base.

Unlike the Software Architecture Specification, Engineering State, and Release State, this chapter focuses on preserving engineering context and implementation knowledge that supports effective decision-making during stabilization and future maintenance.

---


# Document 5 — Supplementary Engineering Knowledge

## Chapter 2 — Engineering Decisions & Coding Standards

**Local OpenClaw (LOC)**
**Engineering Knowledge Reference (EKR)**
**Document Status:** Draft (Pending Final Documentation Freeze)
**Document:** 5 of 5 — Chapter 2 (Part B of IV)

---

# Chapter Metadata

| Property          | Value                                                                                                                   |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Document**      | Supplementary Engineering Knowledge                                                                                     |
| **Chapter**       | Chapter 2 — Engineering Decisions & Coding Standards                                                                    |
| **Purpose**       | Record engineering decisions and coding conventions that guide implementation but are not Architecture Decision Records |
| **Scope**         | Engineering practices and implementation standards                                                                      |
| **Stability**     | Living Document                                                                                                         |
| **Depends On**    | Documents 0–4                                                                                                           |
| **Referenced By** | Future implementation and code reviews                                                                                  |
| **Last Updated**  | Sprint 4 RC-4                                                                                                           |

---

# 1. Purpose

## 1.1 Objective

This chapter documents engineering decisions and implementation conventions that support consistent software development throughout Local OpenClaw.

These decisions are intentionally distinguished from Architecture Decision Records (ADRs).

An ADR defines **what the system is**.

This chapter defines **how the system should be implemented**.

Its purpose is to preserve implementation consistency, improve maintainability, and reduce subjective interpretation during future development.

---

## 1.2 Scope

This chapter records:

* implementation decisions,
* coding standards,
* naming conventions,
* typing philosophy,
* documentation conventions,
* testing philosophy,
* abstraction guidelines,
* dependency practices,
* error handling philosophy.

These conventions apply throughout the codebase unless superseded by a future engineering standard.

---

# 2. Engineering Decision Principles

The following principles guide implementation decisions.

## 2.1 Correctness Before Optimization

Implementation shall prioritize correctness over optimization.

Performance improvements should be introduced only when supported by evidence obtained through measurement or profiling.

Premature optimization should be avoided.

---

## 2.2 Simplicity Before Cleverness

Readable, explicit implementation is preferred over concise but difficult-to-understand code.

Implementation should optimize for long-term maintainability rather than minimizing lines of code.

---

## 2.3 Incremental Development

Implementation should progress through small, independently verifiable changes.

Each change should leave the repository in a stable state before additional work begins.

---

## 2.4 Evidence-Based Changes

Implementation should change only in response to:

* approved implementation work,
* verified compiler errors,
* verified type-checking errors,
* verified test failures,
* verified runtime defects.

Speculative modifications should be avoided.

---

# 3. Coding Standards

## 3.1 Naming Conventions

Implementation should use descriptive, intention-revealing names.

Guidelines include:

* classes use `PascalCase`,
* functions use `snake_case`,
* variables use descriptive `snake_case`,
* constants use `UPPER_SNAKE_CASE`,
* modules use `snake_case`.

Single-character identifiers should be avoided except where universally accepted (for example, simple loop indices).

---

## 3.2 Type Annotations

All public interfaces shall be fully type annotated.

Internal implementation should also use explicit type annotations whenever they improve readability or correctness.

Type hints should prioritize clarity over brevity.

---

## 3.3 Function Design

Functions should:

* perform one clearly defined responsibility,
* have explicit inputs and outputs,
* minimize hidden side effects,
* avoid unnecessary complexity.

Large functions should be decomposed when doing so improves readability without obscuring behavior.

---

## 3.4 Class Design

Classes should represent cohesive responsibilities.

Implementation should favor composition over inheritance.

Inheritance should be introduced only when it models a genuine "is-a" relationship.

---

# 4. Documentation Conventions

## 4.1 Docstrings

Public modules, classes, and functions should include descriptive docstrings.

Docstrings should explain:

* purpose,
* inputs,
* outputs,
* observable behavior.

Implementation details should remain in the implementation rather than the documentation unless they are necessary for understanding the public contract.

---

## 4.2 Comments

Comments should explain **why**, not **what**.

Code should be sufficiently expressive that explanatory comments describing obvious implementation details are unnecessary.

Outdated comments should be removed rather than preserved.

---

## 4.3 Documentation Synchronization

Documentation should remain synchronized with verified implementation.

Documentation should not describe planned functionality as though it has already been implemented.

---

# 5. Error Handling Philosophy

Errors should be:

* explicit,
* meaningful,
* actionable,
* appropriate to the subsystem.

Exception types should communicate the nature of the failure rather than exposing implementation details.

Errors should be propagated to the appropriate boundary rather than silently ignored.

Unexpected conditions should fail predictably.

---

# 6. Dependency Philosophy

Dependencies should remain consistent with the Software Architecture Specification.

Implementation should:

* depend upon stable public interfaces,
* preserve subsystem ownership,
* avoid circular dependencies,
* avoid unnecessary coupling.

Cross-subsystem communication should occur through approved interfaces rather than internal implementation details.

---

# 7. Abstraction Guidelines

Abstractions should exist only when they provide clear engineering value.

New abstractions should generally satisfy one or more of the following:

* multiple implementations are required,
* duplication would otherwise become difficult to maintain,
* subsystem boundaries become clearer,
* testing becomes significantly simpler.

Abstractions should not be introduced solely in anticipation of possible future requirements.

---

# 8. Helper Method Philosophy

Helper methods should:

* encapsulate repeated implementation logic,
* improve readability,
* preserve cohesion,
* avoid obscuring the primary implementation flow.

Implementation should not be fragmented into excessively small helper methods when doing so reduces readability.

---

# 9. Testing Philosophy

Testing should verify externally observable behavior.

Tests should:

* validate public contracts,
* avoid implementation-specific assertions,
* remain deterministic,
* isolate the behavior under test,
* minimize unnecessary mocking.

Behavioral tests should verify subsystem responsibilities rather than internal implementation details.

---

# 10. Review Philosophy

Engineering review should focus on:

* correctness,
* consistency,
* maintainability,
* architectural compliance,
* implementation clarity.

Reviews should distinguish:

* implementation defects,
* documentation defects,
* architectural concerns,
* engineering preferences.

Subjective preferences should not override established engineering standards.

---

# 11. Engineering Decision Maintenance

Engineering decisions documented in this chapter should evolve only when:

* experience demonstrates a better implementation practice,
* project-wide consistency improves,
* the Software Architecture Specification remains unaffected.

Changes to these conventions should preserve compatibility with the architectural principles defined in Document 1.

---

# 12. Chapter Summary

This chapter documents the engineering practices that guide day-to-day implementation of Local OpenClaw.

It defines:

* implementation decision principles,
* coding standards,
* documentation conventions,
* typing practices,
* dependency philosophy,
* abstraction guidelines,
* helper method usage,
* testing philosophy,
* review philosophy,
* and maintenance rules for engineering conventions.

These practices complement the Software Architecture Specification by promoting a consistent, maintainable, and evidence-based implementation approach without introducing additional architectural constraints.

---


# Document 5 — Supplementary Engineering Knowledge

## Chapter 3 — Engineering Lessons

**Local OpenClaw (LOC)**
**Engineering Knowledge Reference (EKR)**
**Document Status:** Draft (Pending Final Documentation Freeze)
**Document:** 5 of 5 — Chapter 3 (Part C of IV)

---

# Chapter Metadata

| Property          | Value                                                                                                                  |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Document**      | Supplementary Engineering Knowledge                                                                                    |
| **Chapter**       | Chapter 3 — Engineering Lessons                                                                                        |
| **Purpose**       | Capture institutional engineering knowledge gained during implementation to improve future development and maintenance |
| **Scope**         | Engineering practices, review outcomes, implementation lessons, and common pitfalls                                    |
| **Stability**     | Living Document                                                                                                        |
| **Depends On**    | Documents 0–4                                                                                                          |
| **Referenced By** | Future implementation sessions, engineering reviews, onboarding                                                        |
| **Last Updated**  | Sprint 4 RC-4                                                                                                          |

---

# 1. Purpose

## 1.1 Objective

This chapter captures engineering knowledge acquired during the implementation of Local OpenClaw that should influence future engineering work.

Unlike the Software Architecture Specification, which defines permanent system design, or the Engineering State, which records implementation progress, this chapter records practical lessons that improve engineering quality and reduce the likelihood of repeating avoidable mistakes.

These lessons represent implementation experience rather than architectural decisions.

---

## 1.2 Scope

This chapter documents:

* engineering lessons,
* implementation practices that proved effective,
* common pitfalls,
* review observations,
* stabilization lessons,
* validation lessons,
* documentation lessons.

These lessons should guide future implementation without redefining the project's architecture.

---

# 2. Architectural Discipline Lessons

## Lesson 1 — Freeze Architecture Before Scaling Implementation

Completing architectural work before large-scale implementation significantly reduced implementation uncertainty.

Stable subsystem ownership, public interfaces, and dependency rules enabled engineering effort to focus on implementation rather than repeated architectural interpretation.

**Guidance**

Major implementation should begin only after architectural responsibilities have been clearly established.

---

## Lesson 2 — Preserve Explicit Ownership

Implementation quality improved when every subsystem had a clearly defined owner.

Questions such as "Where should this logic live?" became significantly easier to answer because responsibilities were already established.

**Guidance**

When adding functionality, identify the owning subsystem first and extend that subsystem rather than distributing logic across multiple areas.

---

## Lesson 3 — Stable Interfaces Reduce Stabilization Cost

Freezing public interfaces early allowed implementation details to evolve without affecting surrounding components.

This reduced ripple effects throughout the codebase.

**Guidance**

Modify internal implementation whenever possible before considering changes to public interfaces.

---

# 3. Implementation Lessons

## Lesson 4 — One File at a Time Produces Better Results

Working on a single file from audit through completion improved implementation quality and reduced unintended side effects.

It also simplified review and validation.

**Guidance**

Complete one implementation objective before moving to the next.

---

## Lesson 5 — Minimal Changes Are Easier to Validate

Small, focused implementation changes are easier to review, understand, and stabilize than broad modifications affecting multiple subsystems.

**Guidance**

Prefer localized changes that solve a single engineering objective.

---

## Lesson 6 — Explicit Code Ages Better

Readable implementation consistently proved easier to validate and maintain than highly condensed or overly abstract code.

**Guidance**

Optimize for future maintainability rather than implementation brevity.

---

# 4. Testing Lessons

## Lesson 7 — Test Public Behavior

Behavioral tests built around public contracts remained stable even when internal implementation evolved.

Implementation-specific assertions created unnecessary maintenance burden.

**Guidance**

Test observable behavior rather than internal implementation details.

---

## Lesson 8 — Runtime Evidence Takes Priority

Engineering assumptions should not become permanent knowledge until confirmed through repository validation or runtime execution.

**Guidance**

When uncertainty exists, rely on execution rather than inference.

---

## Lesson 9 — Separate Unit and Integration Responsibilities

Individual subsystems should validate their own responsibilities.

Cross-subsystem interaction should emerge through stable public contracts rather than tightly coupled integration tests.

**Guidance**

Keep test scope narrow and responsibility-focused.

---

# 5. Documentation Lessons

## Lesson 10 — Documentation Should Have Clear Ownership

The documentation suite remained manageable because each document owned a distinct responsibility.

This minimized duplication and reduced inconsistency.

**Guidance**

Place information in the document responsible for maintaining it rather than duplicating it elsewhere.

---

## Lesson 11 — Architecture and Implementation Should Be Separated

Keeping architectural decisions separate from implementation progress improved clarity and reduced the need to revise stable documentation.

**Guidance**

Architecture should describe the intended system; implementation documents should describe the current repository state.

---

## Lesson 12 — Living Documents Need Stable Boundaries

Documents that evolve during implementation benefit from clearly defined responsibilities and update rules.

**Guidance**

Update only the document responsible for the affected engineering information.

---

# 6. Stabilization Lessons

## Lesson 13 — Validate Before Correcting

Many apparent issues disappear once validation provides objective evidence.

Changing implementation before validation increases the likelihood of introducing unnecessary modifications.

**Guidance**

Run the appropriate validation step before attempting corrective work.

---

## Lesson 14 — Classify Before Fixing

Corrective action is more effective when issues are first classified as implementation, test, documentation, or configuration defects.

**Guidance**

Understand the nature of a problem before modifying the repository.

---

## Lesson 15 — Preserve Stability During RC Phases

Release candidate stabilization should focus on improving correctness rather than expanding functionality.

**Guidance**

Treat release stabilization as a quality phase rather than a development phase.

---

# 7. Common Mistakes to Avoid

The following checklist summarizes mistakes that future implementation should avoid.

### Architecture

* Reopening accepted architectural decisions without evidence.
* Moving responsibilities across subsystem boundaries.
* Introducing parallel architectures.

---

### Implementation

* Modifying unrelated files.
* Combining multiple engineering objectives into a single change.
* Performing speculative refactoring.
* Expanding Version 1 scope during Sprint 4.

---

### Testing

* Testing implementation details instead of public behavior.
* Assuming runtime behavior without validation.
* Coupling behavioral tests to implementation internals.

---

### Documentation

* Duplicating information across documents.
* Mixing architecture with implementation status.
* Recording planned behavior as though already implemented.

---

### Release

* Skipping validation steps.
* Treating assumptions as verified facts.
* Declaring completion before satisfying every release gate.

---

# 8. Long-Term Engineering Guidance

The following principles should continue to guide development beyond Sprint 4.

* Preserve architectural clarity.
* Extend existing subsystem boundaries rather than creating parallel structures.
* Prefer evidence-based engineering decisions.
* Maintain explicit public contracts.
* Keep implementation incremental.
* Keep documentation synchronized with verified implementation.
* Treat validation as an integral engineering activity rather than a final checklist.

These principles support sustainable long-term evolution while preserving the architectural integrity of Local OpenClaw.

---

# 9. Chapter Summary

This chapter records the practical engineering knowledge gained during implementation.

It captures:

* architectural discipline lessons,
* implementation lessons,
* testing lessons,
* documentation lessons,
* stabilization lessons,
* common mistakes to avoid,
* and long-term engineering guidance.

Unlike the preceding documents, these lessons are not normative architectural rules. Instead, they represent accumulated engineering experience intended to improve future implementation quality, maintainability, and consistency.

---


# Document 5 — Supplementary Engineering Knowledge

## Chapter 4 — Engineering Quick Reference

**Local OpenClaw (LOC)**
**Engineering Knowledge Reference (EKR)**
**Document Status:** Draft (Pending Final Documentation Freeze)
**Document:** 5 of 5 — Chapter 4

---

# Chapter Metadata

| Property          | Value                                                                              |
| ----------------- | ---------------------------------------------------------------------------------- |
| **Document**      | Supplementary Engineering Knowledge                                                |
| **Chapter**       | Chapter 4 — Engineering Quick Reference                                            |
| **Purpose**       | Provide a concise operational reference for day-to-day engineering work            |
| **Scope**         | Commands, workflows, reference tables, troubleshooting, and engineering checklists |
| **Stability**     | Living Document                                                                    |
| **Depends On**    | Documents 0–4                                                                      |
| **Referenced By** | Future implementation sessions and repository maintenance                          |
| **Last Updated**  | Sprint 4 RC-4                                                                      |

---

# 1. Purpose

## 1.1 Objective

This chapter serves as a quick-reference appendix for engineers working on Local OpenClaw.

Unlike the preceding chapters, it is intended for frequent consultation during implementation rather than sequential reading.

It consolidates commonly used engineering references while avoiding duplication of architecture, implementation state, or release information maintained elsewhere in the documentation suite.

---

# 2. Documentation Quick Reference

| Information Needed           | Primary Document                                 |
| ---------------------------- | ------------------------------------------------ |
| Executive project status     | Document 0 — Project Manifest                    |
| Software architecture        | Document 1 — Project Foundation                  |
| Current implementation state | Document 2 — Engineering State                   |
| Release readiness            | Document 3 — Release State                       |
| Continuation workflow        | Document 4 — Continuation Package                |
| Engineering conventions      | Document 5 — Supplementary Engineering Knowledge |

Always consult the document responsible for the information rather than relying on historical conversations.

---

# 3. Engineering Workflow Reference

The standard engineering workflow for Sprint 4 is:

```text
Select Current Task
        │
        ▼
Audit Target File
        │
        ▼
Verify Against Documentation
        │
        ▼
Implement Minimum Required Change
        │
        ▼
Review Implementation
        │
        ▼
Validate
        │
        ▼
Stabilize Verified Defects (if required)
        │
        ▼
Proceed to Next Task
```

Implementation should progress sequentially unless a verified defect requires temporary reprioritization.

---

# 4. Validation Reference

Repository-wide validation shall be executed in the following order.

| Order | Validation Activity              |
| ----: | -------------------------------- |
|     1 | Ruff                             |
|     2 | MyPy                             |
|     3 | Pytest                           |
|     4 | Runtime Validation               |
|     5 | Metadata Round-Trip Verification |

Each stage should complete successfully before progressing to the next.

---

# 5. Defect Classification Reference

Every issue identified during validation should be classified before corrective work begins.

| Classification        | Description                                                        |
| --------------------- | ------------------------------------------------------------------ |
| Implementation Defect | Production implementation does not satisfy expected behavior.      |
| Test Defect           | Test expectation is inconsistent with the approved implementation. |
| Documentation Defect  | Documentation no longer reflects verified implementation.          |
| Configuration Defect  | Project configuration prevents successful validation.              |

Corrective work should be proportional to the verified defect.

---

# 6. Escalation Reference

Implementation should continue within the frozen architecture whenever possible.

An architecture review is required only if a verified issue cannot be resolved without violating:

* an accepted ADR,
* a frozen public interface,
* subsystem ownership,
* dependency rules,
* or an architectural invariant.

Engineering uncertainty alone is not sufficient reason to reopen architecture.

---

# 7. Frequently Used Repository Paths

The following paths are commonly referenced during Sprint 4.

| Area                 | Typical Location          |
| -------------------- | ------------------------- |
| Backend source       | `backend/app/`            |
| Backend tests        | `backend/tests/`          |
| Repository subsystem | `backend/app/repository/` |
| Indexing subsystem   | `backend/app/indexing/`   |
| API                  | `backend/app/api/`        |
| Configuration        | `backend/app/core/`       |
| Documentation        | `docs/`                   |

These paths represent logical organization rather than implementation status.

---

# 8. Public Interface Reference

During Sprint 4, the following interface categories are considered stable.

| Category            |
| ------------------- |
| Repository models   |
| Indexing models     |
| Retrieval models    |
| Provider interfaces |
| Storage interfaces  |
| API contracts       |

Detailed definitions remain in **Document 1 — Project Foundation**.

This chapter intentionally references them rather than duplicating them.

---

# 9. Frequently Used Engineering Checklists

## Before Modifying a File

* Confirm the engineering objective.
* Review the existing implementation.
* Verify consistency with Document 1.
* Confirm public interface compatibility.
* Determine the minimum required change.

---

## Before Completing a File

* Implementation complete.
* Public interfaces preserved.
* Documentation updated if required.
* Ready for validation.

---

## Before Repository Validation

* Remaining approved implementation complete.
* Remaining approved behavioral tests complete.
* Repository builds successfully.

---

## Before Sprint Freeze

* Ruff passes.
* MyPy passes.
* Pytest passes.
* Runtime validation complete.
* Metadata validation complete.
* Documentation complete.
* Release gates satisfied.

---

# 10. Common Troubleshooting Guide

| Situation                                    | Recommended Action                                                                 |
| -------------------------------------------- | ---------------------------------------------------------------------------------- |
| Unsure where logic belongs                   | Consult subsystem ownership in Document 1.                                         |
| Unsure whether a change affects architecture | Review accepted ADRs and architectural invariants before modifying implementation. |
| Validation failure                           | Classify the defect before making changes.                                         |
| Runtime behavior differs from assumptions    | Treat runtime evidence as authoritative and stabilize accordingly.                 |
| Documentation inconsistency                  | Update only the document responsible for that information.                         |

---

# 11. Frequently Applied Engineering Principles

During Sprint 4, engineers should consistently apply the following principles.

* Preserve subsystem ownership.
* Preserve public interfaces.
* Prefer explicit implementation.
* Prefer maintainability over cleverness.
* Prefer incremental implementation.
* Prefer evidence over assumptions.
* Validate before stabilizing.
* Keep documentation synchronized with verified implementation.

These principles summarize the engineering philosophy documented throughout the project.

---

# 12. Engineering Bootstrap Checklist

A new implementation session should begin by completing the following checklist.

### Step 1

Read:

* Document 0
* Document 1

to establish project context.

---

### Step 2

Review:

* Document 2
* Document 3

to determine current implementation and release status.

---

### Step 3

Review:

* Document 4

to identify the current implementation task.

---

### Step 4

Consult this document as needed for:

* engineering conventions,
* validation sequence,
* defect classification,
* implementation workflow.

---

### Step 5

Resume implementation from the current working file.

---

# 13. Chapter Summary

This chapter provides a concise operational reference for engineers working on Local OpenClaw.

It consolidates:

* documentation references,
* engineering workflow,
* validation sequence,
* defect classification,
* escalation rules,
* repository paths,
* public interface references,
* engineering checklists,
* troubleshooting guidance,
* engineering principles,
* and a bootstrap checklist.

Its purpose is to reduce context-switching during implementation while keeping architecture, implementation state, and release management responsibilities within their respective authoritative documents.

---

# Document 5 Completion Summary

With the completion of Chapter 4, **Document 5 — Supplementary Engineering Knowledge** is complete.

It provides long-term engineering guidance through four complementary chapters:

### Chapter 1 — Current Engineering Knowledge

* Verified engineering knowledge
* Known implementation issues
* Validation unknowns
* Engineering observations

### Chapter 2 — Engineering Decisions & Coding Standards

* Engineering conventions
* Coding standards
* Typing philosophy
* Testing philosophy
* Documentation standards

### Chapter 3 — Engineering Lessons

* Architectural discipline lessons
* Implementation lessons
* Stabilization lessons
* Common engineering pitfalls
* Long-term engineering guidance

### Chapter 4 — Engineering Quick Reference

* Engineering workflow
* Validation order
* Defect classification
* Escalation rules
* Quick-reference tables
* Checklists
* Troubleshooting guidance
* Session bootstrap checklist

---

