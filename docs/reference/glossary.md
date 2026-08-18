# Glossary

> **Status:** Complete
> **Last Updated:** Sprint 13

---

Key architectural terms. Each term is defined exactly once.

### ChunkBoundary

Line range within a document: `start_line`, `end_line`. Produced by chunking algorithms.

### ChatPrompt

Structured prompt containing a list of `ChatMessage` objects (role + content). Built by `ContextAssembly`.

### ChatProvider

Abstract interface for LLM interaction. Methods: `generate(prompt)`, `stream(prompt)`. Implemented by `OllamaChatProvider`.

### ContextAssembly

Abstract interface for building prompts from retrieved context. The `DefaultContextAssembly` implementation constructs a `ChatPrompt` with system instruction + repository context + user query.

### EmbeddingProvider

Abstract interface for generating embeddings from text. Implemented by `OllamaEmbeddingProvider`.

### IndexedChunk

A `RepositoryChunk` combined with its `EmbeddingVector`. Produced by the Indexing subsystem. Stored in the vector store.

### IndexingResult

Summary of an indexing operation: `scanned_files`, `indexed_files`, `indexed_chunks`, `skipped_files`, `failed_files`.

### Project

Persisted metadata for an opened project. Contains `name`, `root_directory`, `storage_directory`, `created_at`. Persisted to `<root>/.local_openclaw/project.json`.

### ProjectInitializationService

Orchestration service that coordinates project opening, repository indexing, and semantic indexing. Introduced in Sprint 12.1.

### RepositoryChunk

A segment of a repository file produced by the chunker. Contains `chunk_id`, content, metadata, and boundary information.

### RepositoryChunkMetadata

Metadata attached to each chunk: `relative_path`, `language`, `mime_type`, `sha256`.

### RepositoryEntry

A scanned file or directory entry. Contains path, size, language, MIME type, SHA-256, text file flag.

### RepositoryIndex

Result of `RepositoryService.build_index()`. Contains `RepositorySummary` and `list[RepositoryEntry]`.

### RepositoryScanner

Traverses a directory tree, applies ignore rules, returns `RepositoryEntry` objects.

### SearchHit

Raw result from vector store search. Contains `chunk_id`, content, `metadata`, `boundary`, `vector_score`.

### SearchResult

API projection mapped from `SearchHit`. Contains `similarity_score` instead of `vector_score`. Stable contract for API consumers.

### SearchResponse

API response for semantic search. Contains `query` and `list[SearchResult]`.

### Snapshot

Pre-edit file state captured before applying a `ChangeSet`. Used for rollback.

### StorageProvider

Abstract interface for filesystem persistence (project metadata, snapshots, configuration).

### VectorStore

Abstract interface for vector persistence and similarity search. Implemented by `ChromaVectorStore`.

### VectorStoreResolver

Abstract interface for resolving the `VectorStore` for a project root. Persistence identity comes from the opened project, never the process working directory. Implementations: `ProjectChromaStoreResolver` (per-project Chroma stores; returns `None` for projects that have never been indexed), `StaticVectorStoreResolver` (test helper). Defined in `app/indexing/store_resolver.py`.

### ProjectChromaStoreResolver

`VectorStoreResolver` implementation that maps a project root to a `ChromaVectorStore` at `<project root>/.local_openclaw/index/chroma`. Caches one store per project directory; `close_all()` stops all cached Chroma systems and releases their file handles. Defined in `app/indexing/store_resolver.py`.

### Project Storage Directory

The project-local persistence directory: `<project root>/.local_openclaw/`. Contains `project.json` (project metadata), `index/chroma/` (vector store), and `snapshots/` (pre-edit file state). Derived from `Project.root_directory` — see `app/core/storage/locations.py`.
