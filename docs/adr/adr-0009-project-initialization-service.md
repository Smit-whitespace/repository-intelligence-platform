# ADR-0009: ProjectInitializationService

**Status:** Adopted (Sprint 12.1)

**Context:**

Before Sprint 12.1, opening a project (`POST /projects/open`) only persisted project metadata. The user was required to separately trigger indexing. This created a manual step that could be forgotten, leaving projects unindexed and chat unable to provide repository-aware responses.

**Decision:**

Introduce `ProjectInitializationService` — an orchestration layer that calls `ProjectService.open_project()` → `RepositoryService.build_index()` → `IndexingService.index_repository()` in sequence. The service is injected into the API endpoint, replacing direct `ProjectService` usage.

**Consequences:**

Positive:
- Project opening now fully initializes the repository for chat
- No existing service was modified — orchestration is additive
- Clean separation between orchestration and business logic

Negative:
- `build_index()` and `index_repository()` each scan the filesystem independently (duplicate scan)
- Synchronous I/O — large repositories may cause HTTP delay

**Alternatives Considered:**

- Call indexing from ProjectService: rejected — would move orchestration into a business-logic service
- Keep manual indexing: rejected — poor developer experience, easy to forget
- Background task: deferred — adds complexity; can be added later without architectural change
