# Naming Conventions

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Project Names

| Context | Name |
|---------|------|
| Full name | Repository Intelligence Platform (RIP) |
| Historical | Local OpenClaw (LOC) |
| Package | `local-openclaw` |
| Application code | `app` |
| Frontend | `frontend/` |

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
