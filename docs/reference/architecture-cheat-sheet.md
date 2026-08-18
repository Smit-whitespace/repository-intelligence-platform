# Architecture Cheat Sheet

> **Status:** Complete
> **Last Updated:** Sprint 13
> **Reading Time:** 2 minutes
> **Audience:** All contributors

---

## Quick Reference

### Subsystems

| Subsystem | Directory | Key File | Responsibility |
|-----------|-----------|----------|----------------|
| Project Management | `app/projects/` | `service.py`, `initialization_service.py` | Project lifecycle, validation, orchestration |
| Repository | `app/repository/` | `service.py` | Scanning, metadata, chunking |
| Indexing | `app/indexing/` | `service.py`, `indexer.py`, `store_resolver.py` | Embedding, vector persistence |
| Retrieval | `app/indexing/` | `retrieval_service.py` | Project-scoped semantic search |
| Chat | `app/chat/` | `service.py` | Repository-aware conversation |
| Context Assembly | `app/context_assembly/` | `service.py` | Prompt construction |
| Editing | `app/editing/` | `service.py`, `change_applier.py` | Code modification with rollback |
| Storage | `app/core/storage/` | `filesystem.py`, `locations.py` | Filesystem persistence + canonical project layout |
| Vector Store | `app/indexing/` | `chroma_store.py` | Vector persistence + search |
| Vector Store Resolution | `app/indexing/` | `store_resolver.py` | Per-project vector store resolution |
| API | `app/api/routes/` | `projects.py`, `chat.py`, etc. | REST endpoints |

### Ownership Rules

```
✓ Project Management may depend on: Repository, Indexing, Storage
✓ Repository may depend on: (nothing — foundational)
✓ Indexing may depend on: Repository, Storage, EmbeddingProvider, VectorStoreResolver
✓ Retrieval may depend on: EmbeddingProvider, VectorStoreResolver
✓ Chat may depend on: Retrieval, ContextAssembly, ChatProvider
✓ Editing may depend on: Storage, ChatProvider
✗ Chat → Indexing (never)
✗ Retrieval → Indexing (never)
✗ Indexing → Retrieval (never)
✗ Repository → anything non-foundational
✗ Storage → any business logic
```

### Key Interfaces

| Interface | File | Implementations |
|-----------|------|-----------------|
| `EmbeddingProvider` | `app/indexing/providers.py` | `OllamaEmbeddingProvider` |
| `VectorStore` | `app/indexing/stores.py` | `ChromaVectorStore` |
| `VectorStoreResolver` | `app/indexing/store_resolver.py` | `ProjectChromaStoreResolver`, `StaticVectorStoreResolver` |
| `ChatProvider` | `app/chat/providers.py` | `OllamaChatProvider` |
| `ContextAssembly` | `app/context_assembly/providers.py` | `DefaultContextAssembly` |
| `EditingProvider` | `app/editing/providers.py` | `DefaultEditingProvider` |
| `StorageProvider` | `app/core/storage/abstractions.py` | `FileSystemStorage` |

### Core Data Flow

```
Project Open → ProjectService → RepositoryService.build_index() → IndexingService.index_repository()
                                                                                    ↓
User Query → RetrievalService.search() → ContextAssembly.assemble() → ChatProvider.generate()
```

### Dependency Injection

All providers in `app/dependencies/providers.py`:
- Convention: `@lru_cache(maxsize=1)` + `get_<service_name>()`
- Services receive dependencies via constructor injection
- No service instantiates its own dependencies

### Project Initialization (Sprint 12.1+)

```
POST /projects/open
  → ProjectInitializationService.open_project()
    → ProjectService.open_project()        (validate + persist)
    → RepositoryService.build_index()      (scan + enrich_fast)
    → IndexingService.index_repository()   (scan + enrich + load + chunk + embed)
  → Project (ready for chat)
```

### Persistence Identity (Sprint 13)

```
opened Project
    ↓
Project.root_directory / Project.storage_directory
    ↓
<project root>/.local_openclaw/            (project.json, index/chroma/, snapshots/)
    ↓
same store regardless of process CWD
```

Retrieval is project-scoped: searches without `root_directory` (or for unindexed projects) return no results.

### Validation Gates

```bash
# from the backend/ directory
uv run ruff check app tests scripts eval
uv run python -m mypy app
uv run python -m pytest tests -q
```

### Configuration

| Setting (env key) | Default | Notes |
|---------|---------|-------|
| `LOC_SERVER_HOST` / `LOC_SERVER_PORT` | `127.0.0.1` / `8000` | HTTP server |
| `LOC_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `LOC_OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `LOC_OLLAMA_CHAT_MODEL` | `qwen3:8b` | Chat model |
| `LOC_CHROMA_COLLECTION_NAME` | `repository_chunks` | Chroma collection name |
| Persist directory | `<project root>/.local_openclaw/index/chroma` | Derived from the opened project — not configurable |

> Legacy keys `LOC_STORAGE_ROOT_DIRECTORY` and `LOC_CHROMA_PERSIST_DIRECTORY` are ignored (kept in the sample `.env` only as historical documentation).

---

## Related

| Document | Link |
|----------|------|
| Full Glossary | [glossary.md](glossary.md) |
| System Overview | [../architecture/system-overview.md](../architecture/system-overview.md) |
| Dependency Map | [dependency-map.md](dependency-map.md) |
| START-HERE | [../START-HERE.md](../START-HERE.md) |
