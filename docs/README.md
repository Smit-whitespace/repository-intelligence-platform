# Repository Intelligence Platform — Documentation

## Quick Start

| If you're... | Start here |
|-------------|------------|
| **New to the project** | [START-HERE.md](START-HERE.md) — canonical onboarding guide |
| **Looking for a specific term** | [Reference/Glossary](reference/glossary.md) |
| **Setting up development** | [Development/Environment](development/environment.md) |
| **Need a quick reminder** | [Reference/Architecture Cheat Sheet](reference/architecture-cheat-sheet.md) |

## Navigation

| Directory | Purpose |
|-----------|---------|
| [START-HERE.md](START-HERE.md) | Canonical onboarding guide |
| [vision/](vision/) | Project identity, purpose, principles, and long-term direction |
| [architecture/](architecture/system-overview.md) | System architecture, subsystem responsibilities, ownership, and invariants |
| [architecture/repository-lifecycle.md](architecture/repository-lifecycle.md) | End-to-end runtime lifecycle |
| [architecture/diagrams/](architecture/diagrams/) | Reusable Mermaid architecture diagrams |
| [adr/](adr/) | Architecture Decision Records (17) |
| [api/](api/) | API reference — endpoints, schemas, contracts |
| [development/](development/) | Setup, conventions, validation, testing, release process, extension guides |
| [roadmap/](roadmap/) | Forward plan through Release Candidate |
| [reference/](reference/) | Glossary, cheat sheet, terminology, naming conventions, dependency map, configuration, timeline |
| [sprints/](sprints/) | Sprint freeze documentation — historical and current |

## Historical Documentation (Sprint 4 era)

The `docs/Info docs/`, `docs/release notes/`, and `docs/Sprint Goals/` directories contain the original Sprint 4 documentation set. These are retained as historical records. All new documentation lives under this hierarchy.

## Principles

- The implementation is the single source of truth. Documentation follows implementation.
- Each topic has one authoritative location. Cross-references replace duplication.
- Documentation answers: what exists, why it exists, how it works, and how to extend it.
