# Bug Report: Cross-Project Context Contamination in Chat

**Status:** Root cause identified, fix not implemented
**Report Date:** 2026-07-29
**Reported by:** Instrumentation trace

---

## Summary

Switching from Repository A to Repository B causes the assistant to answer using Repository A's indexed content. The retrieval pipeline has **no project-scoping mechanism** — every chat query searches all indexed chunks across all repositories.

---

## Root Cause

The chat pipeline lacks any project filtering at every layer:

```
Chat API (no project parameter)
  → ChatService (no project context)
    → RetrievalService.search() (no filter parameter)
      → ChromaVectorStore.search() (no ChromaDB 'where' filter)
        → Returns chunks from ALL indexed repositories
```

### Evidence (by layer)

#### 1. Chat API Endpoint — `backend/app/api/routes/chat.py:82-105`

```python
def stream_chat(
    query: str = Query(...),       # ← ONLY query. No project_id/root_directory.
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
```

The endpoint accepts **only a `query` string**. There is no way to specify which project the user is asking about. The `ChatRequest` model (`backend/app/chat/schemas.py:11`) also contains only a `query` field.

**Verification:** Instrumentation log at endpoint:
```
[INSTRUMENT] chat() called — query='Explain this repo'
[INSTRUMENT] No project/root_directory parameter in endpoint
```

#### 2. ChatService — `backend/app/chat/service.py:48-73`

```python
search_response = self._retrieval_service.search(
    SearchQuery(query=request.query),  # ← No project filter
)
```

The service has no concept of the active project. It passes only the query string to the retrieval service.

**Verification:**
```
[INSTRUMENT] ChatService has NO active project reference — no project_id or root_directory stored
```

#### 3. RetrievalService — `backend/app/indexing/retrieval_service.py:27-66`

```python
def search(self, query: SearchQuery) -> SearchResponse:
    ...
    search_hits = self._vector_store.search(
        query_embedding=query_embedding,
        limit=query.limit,              # ← No filter parameter
    )
```

The `SearchQuery` model (`backend/app/indexing/retrieval_models.py:11`) has only `query` and `limit`. The `VectorStore` abstraction (`backend/app/indexing/stores.py:27`) also has only `query_embedding` and `limit` — no filter/collection parameter.

**Verification:**
```
[INSTRUMENT] SearchQuery has NO project/collection filter — filtering ALL indexed chunks across ALL projects
```

#### 4. ChromaVectorStore — `backend/app/indexing/chroma_store.py:73-91`

```python
raw_result = self._collection.query(
    query_embeddings=[...],
    n_results=limit,                  # ← No 'where' filter
)
```

The ChromaDB `query()` call has **no `where` parameter**. Every query searches the single hardcoded `"repository_chunks"` collection across all stored documents.

The `ChromaSettings` model (`backend/app/core/config/models.py:40-47`) defines a **single collection name**:
```python
class ChromaSettings(BaseModel):
    persist_directory: Path = Path(".local_openclaw/index/chroma")
    collection_name: str = "repository_chunks"  # ← Shared by all projects
```

**Verification:**
```
[INSTRUMENT] ChromaVectorStore.search() — collection='repository_chunks', limit=10, NO where filter applied
[INSTRUMENT] *** KEY OBSERVATION: ChromaDB query has no 'where' filter — retrieving from ALL projects ***
```

#### 5. Chunk Metadata Has No Project Identifier

`RepositoryChunkMetadata` (`backend/app/repository/models.py:70-80`) stores:
- `relative_path`
- `language`
- `mime_type`
- `sha256`

**No `root_directory` or project identifier field exists.**

When chunks are stored in ChromaDB via `chroma_store.py:44-71`, the metadata written is:
```python
metadatas=[{
    **chunk.metadata.model_dump(mode="json"),   # relative_path, language, mime_type, sha256
    **chunk.boundary.model_dump(mode="json"),   # start_line, end_line, chunk_type
}]
```

No project/root_directory is persisted.

---

## Answering the Verification Questions

| Question | Answer |
|----------|--------|
| **Is vector search filtered by active project?** | **No.** `ChromaVectorStore.search()` calls `self._collection.query()` with no `where` filter. The `VectorStore` abstraction has no filter parameter. All indexed chunks are searched regardless of project. |
| **What happens if retrieval returns zero chunks?** | **The correct path exists.** `ContextAssembly.assemble()` filters by similarity (>=0.3), deduplicates, and if nothing remains, returns the `_INSTRUCTION_WITHOUT_CONTEXT` prompt which says: *"No repository context is available for this query"* and instructs the LLM not to fabricate. **However, this path is never reached in practice** because retrieval finds chunks from other projects, so the filter passes non-empty results. |
| **Is previous chat history reused?** | **No.** Each call to `ChatService.chat()` or `.stream()` builds a fresh `ChatPrompt` with system messages + the current user query. No message history is stored or passed to the LLM. |
| **Is previous retrieval cached?** | **No.** There is no caching layer. `RetrievalService.search()` embeds the query and queries ChromaDB fresh every time. Dependencies are `@lru_cache` singletons (same service instance) but no results are cached. |
| **Does ContextAssembly reuse previous repository context?** | **No.** `DefaultContextAssembly.assemble()` is stateless. It processes whatever `SearchResult` list is passed on each invocation. |

---

## Why the Bug Occurs

1. User opens Repository A (RIP). Backend indexes all of Repository A's code into the **shared** ChromaDB collection `"repository_chunks"`.
2. User asks questions about Repository A. Retrieval finds Repository A's chunks (since they're the only ones indexed). Answers are correct.
3. User opens Repository B (Gitprolizer). Backend indexes Repository B into the **same** collection. But Gitprolizer has almost no source code, so few chunks are added.
4. User asks a question about Repository B (e.g., "Explain this repo"). Retrieval searches the **entire** collection, finds **Repository A's chunks** (since they're more numerous and semantically dense), returns those.
5. ContextAssembly includes Repository A's code in the prompt. The assistant answers using Repository A's information — **cross-project contamination**.

---

## Minimal Fix

The fix requires changes in **4 layers**:

### 1. ChromaVectorStore — Accept a `where` filter

Add an optional `collection_filter` parameter to `VectorStore.search()` and pass it as ChromaDB's `where` parameter:

```python
def search(
    self,
    query_embedding: EmbeddingVector,
    limit: int = 10,
    where: dict | None = None,        # ← new
) -> list[SearchHit]:
    ...
    self._collection.query(
        query_embeddings=[...],
        n_results=limit,
        where=where,                  # ← pass filter
    )
```

### 2. Persist Root Directory in Chunk Metadata

Add a `root_directory` field to `RepositoryChunkMetadata` and populate it when indexing:

```python
class RepositoryChunkMetadata(BaseModel):
    relative_path: Path
    root_directory: Path              # ← new
    language: str | None
    mime_type: str | None
    sha256: str
```

### 3. RetrievalService — Accept and Pass Project Filter

Add an optional `root_directory` parameter to `SearchQuery` and pass it through to the vector store:

```python
class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    root_directory: str | None = None  # ← new
```

In `RetrievalService.search()`:
```python
where = {"root_directory": query.root_directory} if query.root_directory else None
search_hits = self._vector_store.search(
    query_embedding=query_embedding,
    limit=query.limit,
    where=where,
)
```

### 4. Chat API — Accept Project Context

Add `root_directory` parameter to the chat endpoint and pass it through to `ChatService` → `SearchQuery`:

```python
def stream_chat(
    query: str = Query(...),
    root_directory: str | None = Query(None),  # ← new
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
```

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking change to `VectorStore` abstraction | Low — single implementation (Chroma) | Update interface and all callers |
| Indexed chunks from before the fix need re-indexing | Medium — existing DB has no `root_directory` metadata | Migration script or `clear()` + re-index |
| Frontend needs to pass `root_directory` to chat API | Low — frontend already has `activeProject.root_directory` | Add to chat page request |

---

## Instrumentation Files Modified (temporary, revert before fixing)

| File | Change |
|------|--------|
| `backend/app/api/routes/chat.py` | Log endpoint call with no project context |
| `backend/app/chat/service.py` | Log missing active project reference |
| `backend/app/indexing/retrieval_service.py` | Log search with no filters + dump chunk metadata |
| `backend/app/indexing/chroma_store.py` | Log missing `where` filter in ChromaDB query |
| `backend/app/context_assembly/service.py` | Log filtering steps + final assembled context |
