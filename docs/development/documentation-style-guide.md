# Documentation Style Guide

> **Status:** Complete
> **Last Updated:** Sprint 12.1
> **Reading Time:** 3 minutes
> **Audience:** Documentation contributors

---

## Executive Summary

This guide defines the conventions for all documentation in this repository. Following these conventions ensures consistency, navigability, and long-term maintainability.

---

## Document Layout

Every major document should follow this structure:

```markdown
# Title

> **Status:** Complete | Scaffold
> **Sprint Introduced:** Sprint N
> **Last Updated:** Sprint N
> **Reading Time:** X minutes
> **Audience:** Target readers
> **Prerequisites:** [Link](...)

---

## Executive Summary

Concise overview readable in under two minutes.

## (Content sections per document standard)

---

## Related Documents

| Document | Link |
|----------|------|
| Name | [link](...) |
```

## Metadata Block

Place the metadata block immediately after the title. Use the format:

```markdown
> **Status:** Complete
> **Sprint Introduced:** Sprint 12.1
> **Last Updated:** Sprint 12.1
> **Reading Time:** 3 minutes
> **Audience:** Backend contributors
> **Prerequisites:** [System Overview](../architecture/system-overview.md)
```

## Callout Style

Use GitHub Markdown callouts consistently:

| Callout | Usage |
|---------|-------|
| `> [!NOTE]` | General information |
| `> [!TIP]` | Recommended extension pattern |
| `> [!IMPORTANT]` | Architectural invariant |
| `> [!WARNING]` | Violation breaks architecture |
| `> [!HISTORY]` | Introduced in Sprint X |

## Diagrams

- Use Mermaid for all diagrams
- Place diagrams inline in Markdown files
- Keep diagrams simple and readable
- Prefer `sequenceDiagram` for lifecycle flows
- Prefer `graph LR` or `graph TD` for architecture relationships
- Reusable diagrams in `architecture/diagrams/README.md`

## Cross-References

- Every document should link to related documents
- Use relative paths: `[Project Management](architecture/backend/project-management.md)`
- Reference ADRs as: `[ADR-0009](../adr/adr-0009-project-initialization-service.md)`
- Reference APIs as: `[POST /projects/open](../../api/README.md)`

## Naming

- Files: `kebab-case.md`
- Headings: Sentence case
- ADR files: `adr-NNNN-title-with-dashes.md`
- Archive historical sprint docs as `sprint-N.md`

## Writing Style

- Concise technical writing
- Short paragraphs
- Tables for comparisons
- Bullet lists for responsibilities
- Diagrams for architecture
- Avoid implementation-level narration
- Document what exists, why it exists, how it works, how to extend it

## Content Rules

- **No duplication.** If a concept is documented in one place, reference it rather than re-explaining it.
- **No speculation.** Document only what exists and why decisions were made.
- **No line-by-line code explanations.** Document architecture, not implementation.
- **Glossary terms are defined once.** Use `[Glossary](../reference/glossary.md)` references.
- **Subsystem boundaries are explicit.** Every subsystem doc has an allowed/forbidden responsibilities table.

## Quality Checklist

Every document should satisfy:

- [ ] Executive Summary
- [ ] Reading Metadata
- [ ] Purpose
- [ ] Responsibilities (with ownership table for subsystem docs)
- [ ] Architecture diagram (when applicable)
- [ ] Lifecycle diagram (when applicable)
- [ ] Key Files or Components
- [ ] Invariants (callout style)
- [ ] Extension Points
- [ ] Why This Design
- [ ] Known Limitations
- [ ] Related Documents with cross-references
