# Naming Conventions

> **Status:** Complete
> **Last Updated:** Sprint 13

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

Public identity is **Repository Intelligence Platform (RIP)**. Some internal compatibility identifiers from the Local OpenClaw era were intentionally retained:

| Identifier | Status | Where it appears |
|------------|--------|------------------|
| `.local_openclaw` | Active internal storage directory | `<project root>/.local_openclaw/` (project metadata, Chroma index, snapshots) |
| `LOC_` | Active environment variable prefix | `LOC_SERVER_PORT`, `LOC_OLLAMA_*`, `LOC_CHROMA_*`, `LOC_INDEXING_*` |
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
- Filesystem storage: `.local_openclaw/` directory in project root
