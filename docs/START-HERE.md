# Start Here

> **Reading Time:** 5 minutes
> **Audience:** New contributors
> **Prerequisites:** None

---

## Welcome

Repository Intelligence Platform (RIP) is an offline-first, repository-aware AI coding assistant. This guide will get you oriented with the codebase, architecture, and documentation.

---

## Quick Navigation

| If you want to... | Start here |
|-------------------|-----------|
| Understand what this project is | [Vision](vision/README.md) |
| Understand the system architecture | [Architecture Overview](architecture/system-overview.md) |
| Set up your development environment | [Environment Setup](development/environment.md) |
| Understand the project lifecycle | [Repository Lifecycle](architecture/repository-lifecycle.md) |
| See the codebase structure | [Repository Tree](reference/repository-tree.md) |
| Learn coding standards | [Coding Standards](development/standards.md) |
| Run tests and validation | [Validation Workflow](development/validation.md) |
| Understand a specific subsystem | [Architecture docs](architecture/system-overview.md) |
| Find a glossary term | [Glossary](reference/glossary.md) |
| See the roadmap | [Roadmap](roadmap/) |
| Quick reference | [Architecture Cheat Sheet](reference/architecture-cheat-sheet.md) |

---

## Documentation Hierarchy

```
docs/
├── START-HERE.md              ← YOU ARE HERE
├── README.md                  Navigation hub
├── vision/                    Project identity and principles
├── architecture/              System and subsystem architecture
│   ├── system-overview.md     Top-level architecture map
│   ├── repository-lifecycle.md End-to-end runtime lifecycle
│   ├── evolution.md           Architecture evolution by sprint
│   ├── backend/               Subsystem docs (8 files)
│   ├── frontend/              Frontend architecture
│   └── diagrams/              Reusable Mermaid diagrams
├── adr/                       Architecture Decision Records (17)
├── api/                       API reference
├── development/               Setup, standards, validation, guides
├── roadmap/                   Forward plan through RC
├── reference/                 Glossary, cheat sheet, naming, config
└── sprints/                   Sprint freeze documentation
```

---

## Recommended Reading Path

### New to the project

1. **START-HERE.md** (this document)
2. [Vision](vision/README.md) — 5 min
3. [Architecture Overview](architecture/system-overview.md) — 4 min
4. [Architecture Cheat Sheet](reference/architecture-cheat-sheet.md) — 2 min

### Setting up development

5. [Environment Setup](development/environment.md) — 5 min
6. [Repository Tree](reference/repository-tree.md) — 3 min
7. [Coding Standards](development/standards.md) — 3 min

### Deep dive by subsystem

8. Read the architecture doc for your subsystem of interest:
   - [Project Management](architecture/backend/project-management.md)
   - [Repository](architecture/backend/repository.md)
   - [Indexing](architecture/backend/indexing.md)
   - [Retrieval](architecture/backend/retrieval.md)
   - [Chat](architecture/backend/chat.md)
   - [Editing](architecture/backend/editing.md)
   - [Storage](architecture/backend/storage.md)

### Understanding decisions

9. Browse [ADRs](adr/) — each is a 2-minute read
10. [Architecture Evolution](architecture/evolution.md) — 3 min

### Contributing

11. [Validation Workflow](development/validation.md) — 2 min
12. [Testing Guide](development/testing.md) — 3 min
13. Extension guides in [development/guides/](development/guides/)

---

## Key Concepts

- **Offline-first** — Everything runs locally. No cloud required.
- **Subsystem ownership** — Each subsystem owns one responsibility. Boundaries are explicit.
- **Orchestration, not business logic** — Services like `ProjectInitializationService` delegate work, they don't implement domain rules.
- **Dependency injection** — All services receive dependencies via constructors. Wiring is centralized in `providers.py`.
- **Project-root persistence identity** — All project-local persistence (metadata, Chroma index, snapshots) lives under `<project root>/.local_openclaw/`, derived from the opened project — never from the process working directory.

---

## Related

| Document | Link |
|----------|------|
| README | [README.md](README.md) |
| Documentation Style Guide | [development/documentation-style-guide.md](development/documentation-style-guide.md) |
