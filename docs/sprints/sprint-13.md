# Sprint 13 — CWD-Independent Project Persistence

## Sprint Objective

Fix project persistence and index resolution so that storage identity is derived from the opened project root (`Project.root_directory` / `Project.storage_directory`) — never from the backend process working directory (CWD). Before this sprint, index resolution could depend on the process CWD, producing a wrong and empty store at e.g. `<project root>\backend\.local_openclaw\index\chroma` when the backend was started from the `backend/` directory.

## Architecture Changes

Introduce a project-scoped vector store resolver; vector store resolution now flows from the opened project root.

```
Before Sprint 13:
    backend process CWD
        ↓
    relative Chroma persist path
        ↓
    backend\... (or launch-directory) .local_openclaw\index\chroma
        ↓
    wrong / empty store; retrieval misses the project index

After Sprint 13:
    opened Project
        ↓
    Project.root_directory → Project.storage_directory
        ↓
    project-local persistence  (<project root>\.local_openclaw\index\chroma)
        ↓
    same Chroma store regardless of process CWD
```

Canonical project-local layout (each opened project root):

```
<project root>/
└── .local_openclaw/
    ├── project.json
    ├── index/
    │   └── chroma/          ← ChromaDB persistence (VectorStore)
    └── snapshots/           ← editing snapshots
```

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `backend/app/core/storage/locations.py` | Created | Canonical project storage layout helpers (`project_storage_directory`, `project_chroma_directory`, `project_metadata_path`) |
| `backend/app/indexing/store_resolver.py` | Created | `VectorStoreResolver` protocol; `ProjectChromaStoreResolver` (per-project store with `create=False` short-circuit); `StaticVectorStoreResolver` (test helper); `close_all()` for Windows file-handle hygiene |
| `backend/app/indexing/chroma_store.py` | Modified | Constructor takes `persist_directory` + `collection_name`; added `close()` releasing ChromaDB system resources and file handles |
| `backend/app/indexing/indexer.py` | Modified | `RepositoryIndexer` resolves the store via `VectorStoreResolver.for_project(root_directory, create=True)`; requires `root_directory` in chunk metadata |
| `backend/app/indexing/retrieval_service.py` | Modified | `RetrievalService` resolves the store via `VectorStoreResolver`; queries without `root_directory` (or for unopened projects) return no results; scoped `where` filter on `root_directory` |
| `backend/app/indexing/retrieval_models.py` | Modified | `SearchQuery` carries `root_directory` |
| `backend/app/dependencies/providers.py` | Modified | `get_vector_store_resolver()`; indexer/retrieval wired through the resolver; editing snapshot store factory per repository root; `get_storage`/`get_vector_store`/`get_snapshot_store` removed |
| `backend/app/projects/service.py` | Modified | Project storage directory via `locations.project_storage_directory(root_directory)` |
| `backend/app/editing/service.py` | Modified | `snapshot_store_factory` resolved per repository root; repository root validated (exists + is directory) before any project-local storage is created |
| `backend/app/api/routes/chat.py` | Modified | Chat request/stream accept `root_directory`; scoped retrieval |
| `backend/app/core/config/models.py`, `provider.py` | Modified | `ChromaSettings` reduced to `collection_name` (persist directory intentionally non-configurable); unknown env keys ignored (legacy `LOC_STORAGE_ROOT_DIRECTORY`, `LOC_CHROMA_PERSIST_DIRECTORY` inert) |
| `backend/app/repository/ignore.py` | Modified | `.local_openclaw` and `.repository-intelligence-platform` excluded from repository scans |
| `backend/scripts/check_chroma.py` | Modified | Updated to the new `ChromaVectorStore` constructor |
| `backend/eval/runner.py` | Modified | `create_retrieval_evaluator` wraps the vector store in `StaticVectorStoreResolver`; evaluator accepts an optional `root_directory` to scope searches |
| Tests | Modified/Created | Scoped-retrieval tests, resolver-constructor updates, CWD-independence coverage; see `backend/tests/` |

## Vertical Slices

| Slice | Scope | Status |
|-------|-------|--------|
| 1 — Project-root persistence identity | Store resolution derives from `Project.root_directory` / `storage_directory` | ✅ |
| 2 — Project-scoped retrieval | Retrieval without an opened project returns no results; `where` filter on `root_directory` | ✅ |
| 3 — Per-project snapshot stores | Editing snapshot storage resolved per repository root | ✅ |
| 4 — Store lifecycle | `ChromaVectorStore.close()` + `ProjectChromaStoreResolver.close_all()` release file handles (Windows) | ✅ |
| 5 — Runtime acceptance | Backend started from repo root **and** from `backend/` both resolve `<project root>\.local_openclaw\index\chroma` | ✅ |

## Runtime Verification

| Test | Result |
|------|--------|
| Backend started with CWD = repository root; project opened | ✅ 288 files, 273 text files, 1431 chunks created; repository-aware chat returned context-grounded results |
| Backend started with CWD = `backend/`; same project reopened | ✅ 288 files discovered, 1431 chunks created, same project root and persistence location returned |
| Canonical persistence location | ✅ `<project root>\.local_openclaw\index\chroma` in both runs |
| Incorrect CWD-dependent location | ✅ `<project root>\backend\.local_openclaw\index\chroma` not created or written |
| Historical store | ✅ `.repository-intelligence-platform\index\chroma` untouched (hash and mtime unchanged) |

The `.repository-intelligence-platform/index/chroma` store contains stale data associated with the former `A:\Personal Projects\Projects\local-openclaw` path. It is **not** the current RIP index and was intentionally not migrated, rewritten, merged, or deleted during this sprint.

## Validation Results

| Gate | Result | Notes |
|------|--------|-------|
| Ruff | ✅ All checks passed | — |
| MyPy | ✅ No issues | `uv run python -m mypy app` from `backend/` (90 source files) |
| Pytest | ✅ 254 passed | 3 consecutive full-suite runs |
| Runtime CWD-independence | ✅ Passed | See Runtime Verification |

## Known Technical Debt

- **No migration of historical indexes**: old data under `.repository-intelligence-platform/` (and any CWD-dependent stores) is intentionally left in place and out of scope.
- **Full re-index on every open**: opening a project re-indexes the repository (no incremental indexing).
- **Per-project caches held by the resolver**: `ProjectChromaStoreResolver` caches one Chroma client per project directory for the process lifetime; `close_all()` exists for tests and cleanup but is not wired to shutdown hooks.
- **`clear()`/re-index semantics**: re-index upserts into the existing per-project collection.

## Deferred Work

- Wire resolver `close_all()` into backend shutdown/teardown.
- Incremental indexing (index only changed files on open).
- Historical-index migration policy for pre-Sprint-13 stores.

## Lessons Learned

- **Persistence identity must come from domain state, not process state**: deriving Chroma paths from the CWD makes the same application open different stores depending on launch directory. `Project.root_directory` is the single source of truth.
- **Chroma 1.x clients hold file handles for the process lifetime**: on Windows, removing a project directory requires stopping the ChromaDB system (`System.stop()`) and clearing the shared system cache; the shared cache must be cleared only after all stores are stopped, otherwise later lookups fail for previously cached identifiers.
- **Environment quirks belong in startup docs, not workarounds in code**: `uv` on Windows fails to canonicalize script paths when invoked from the repository root; the validated workaround is launching through the project's Python 3.12 environment directly, or running `uv` from `backend/`.
- **Validating a repository root before creating storage prevents materialization side effects**: a nonexistent root would otherwise be "created" by the storage factory during an editing apply/rollback (wrong 200 instead of 400).

---

**Sprint 13 is now FROZEN.**