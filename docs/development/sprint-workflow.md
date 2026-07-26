# Sprint Workflow

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Overview

Each sprint follows an objective → implementation → validation → freeze cycle.

## Sprint Structure

```
1. Objective Definition
   - Define sprint goal
   - Identify vertical slices
   - Freeze scope — no expansion during sprint

2. Slice Implementation
   - One slice at a time
   - Audit before modifying code
   - Smallest correct change
   - Validate after each slice

3. Quality Gates
   - Ruff check
   - MyPy check
   - Pytest

4. Sprint Freeze
   - Produce freeze report
   - Commit and tag
   - Declare frozen

5. Documentation
   - Update sprint document in docs/sprints/
   - Update architecture docs if needed
   - Update ADRs if new decisions were made
```

## Principles

- **Architecture drives implementation.** No redesign during implementation.
- **One responsibility per change.** No opportunistic refactoring.
- **Stabilize before extending.** Fix defects before adding features.
- **Evidence-based engineering.** Decisions based on demonstrated need, not speculation.
- **Subsystem boundaries are frozen.** No responsibility migration between slices.

## Freeze Rules

- Once frozen, a sprint's implementation is immutable
- Post-freeze changes require a new sprint or ADR
- Historical sprint documents are not rewritten
