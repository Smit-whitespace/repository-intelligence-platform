# Naming Conventions

> **Status:** Complete
> **Last Updated:** Sprint 14

---

## Project Names

| Context | Name |
|---------|------|
| Full name | Repository Intelligence Platform (RIP) |
| Historical | Local OpenClaw (LOC) |
| Public repository | `repository-intelligence-platform` |
| Application code | `app` |
| Frontend | `frontend/` |

### Public vs. Internal Identifiers

Public identity is **Repository Intelligence Platform (RIP)**. The last identifiers from the Local OpenClaw era were renamed in Sprint 14 ([ADR-0021](../adr/adr-0021-rip-storage-and-settings-names.md)):

| Identifier | Status | Where it appears |
|------------|--------|------------------|
| `.rip` | Active storage directory | `<project root>/.rip/` (project metadata, Chroma index, snapshots) and `~/.rip/` (API token, integrity key, `models.json`) |
| `RIP_` | Active environment variable prefix | `RIP_SERVER_PORT`, `RIP_OLLAMA_*`, `RIP_CHROMA_*`, `RIP_INDEXING_*` |
| `.local_openclaw` | Former storage directory | Renamed to `.rip` automatically on first use; still protected and never indexed |
| `LOC_` | Former environment variable prefix | Still read, with a warning, when the `RIP_` name is not set |
| `local-openclaw` | Historical (package/logger names in legacy references) | Historical docs and records |

> [!NOTE] `.repository-intelligence-platform` appears only as a **stale historical index store** from the pre-Sprint-13 era. It is not the current RIP index and is not described as active.

## Module Naming

- All lowercase, snake_case
- Single responsibility per module
- Module name describes responsibility: `service.py`, `models.py`, `providers.py`, `stores.py`

## Class Naming

- PascalCase
- Interface classes end with the role: `EmbeddingProvider`, `VectorStore`, `StorageProvider`
- Implementation classes may be prefixed: `OllamaEmbeddingProvider`, `ChromaVectorStore`
- Domain models are plain nouns: `Project`, `RepositoryChunk`, `SearchResult`

## File Organization

- Each subsystem has its own package under `backend/app/`
- Each package contains: `service.py`, `models.py`, `providers.py`, `exceptions.py`, `schemas.py`
- API routes in `backend/app/api/routes/`

## API Naming

- Endpoint paths: lowercase, kebab-case for multi-word: `/repository/index`, `/chat/stream`
- Operation IDs: camelCase: `openProject`, `getRepositoryIndex`
- Query parameters: snake_case

## Database / Collection Naming

- Vector collections: named by the app (ChromaDB manages internally)
- Filesystem storage: `.rip/` directory in project root
