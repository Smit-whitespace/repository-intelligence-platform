# Architecture Cheat Sheet

> **Status:** Complete
> **Last Updated:** Sprint 12.1
> **Reading Time:** 2 minutes
> **Audience:** All contributors

---

## Quick Reference

### Subsystems

| Subsystem | Directory | Key File | Responsibility |
|-----------|-----------|----------|----------------|
| Project Management | `app/projects/` | `service.py`, `initialization_service.py` | Project lifecycle, validation, orchestration |
| Repository | `app/repository/` | `service.py` | Scanning, metadata, chunking |
| Indexing | `app/indexing/` | `service.py`, `indexer.py` | Embedding, vector persistence |
| Retrieval | `app/indexing/` | `retrieval_service.py` | Semantic search |
| Chat | `app/chat/` | `service.py` | Repository-aware conversation |
| Context Assembly | `app/context_assembly/` | `service.py` | Prompt construction |
| Editing | `app/editing/` | `service.py`, `change_applier.py` | Code modification with rollback |
| Storage | `app/core/storage/` | `filesystem.py` | Filesystem persistence |
| Vector Store | `app/indexing/` | `chroma_store.py` | Vector persistence + search |
| API | `app/api/routes/` | `projects.py`, `chat.py`, etc. | REST endpoints |

### Ownership Rules

```
✓ Project Management may depend on: Repository, Indexing, Storage
✓ Repository may depend on: (nothing — foundational)
✓ Indexing may depend on: Repository, Storage, EmbeddingProvider, VectorStore
✓ Retrieval may depend on: EmbeddingProvider, VectorStore
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

### Validation Gates

```bash
uv run ruff check backend/
uv run mypy backend/app/
uv run pytest
```

### Configuration

| Setting | Default |
|---------|---------|
| `storage.root_directory` | `~/.local-openclaw` |
| `ollama.base_url` | `http://localhost:11434` |
| `ollama.embedding_model` | `nomic-embed-text` |
| `ollama.chat_model` | `qwen3:8b` |
| `chroma.persist_directory` | `{storage.root_directory}/chroma` |

---

## Related

| Document | Link |
|----------|------|
| Full Glossary | [glossary.md](glossary.md) |
| System Overview | [../architecture/system-overview.md](../architecture/system-overview.md) |
| Dependency Map | [dependency-map.md](dependency-map.md) |
| START-HERE | [../START-HERE.md](../START-HERE.md) |
