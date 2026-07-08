# Document 1 — Project Foundation

## Chapter 2 — System Architecture

**Local OpenClaw (LOC)**
**Software Architecture Specification**
**Document Status:** Authoritative
**Document:** 2 of 5

---

# 1. Overall System Architecture

## Architectural Overview

Local OpenClaw is organized as a collection of **well-defined subsystems**, each owning a single architectural responsibility. Communication between subsystems occurs only through stable public contracts, minimizing coupling and allowing each subsystem to evolve independently.

The architecture follows a layered approach in which repository understanding forms the foundation upon which indexing, retrieval, memory, editing, and user interaction are built.

Core architectural characteristics include:

* Offline-first operation
* Explicit subsystem ownership
* Stable public interfaces
* Filesystem-based persistence
* Local AI execution
* Incremental extensibility through composition rather than redesign

---

## Architectural Layers

```text
+------------------------------------------------------+
|                  User Interface Layer                |
|  React • Monaco • Zustand • TanStack Query          |
+------------------------------------------------------+
                       │
                       ▼
+------------------------------------------------------+
|                 Application API Layer                |
|      FastAPI • REST • SSE • Background Tasks        |
+------------------------------------------------------+
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
+----------------+ +---------------+ +----------------+
| Repository     | | Memory        | | Editing        |
| Understanding  | |               | | Engine         |
+----------------+ +---------------+ +----------------+
        │
        ▼
+------------------------------------------------------+
|              Repository Intelligence                 |
|  Scanner → Loader → Parser → Chunker               |
+------------------------------------------------------+
                       │
                       ▼
+------------------------------------------------------+
|          Semantic Indexing & Retrieval              |
| Ollama → Embeddings → ChromaDB → Search            |
+------------------------------------------------------+
                       │
                       ▼
+------------------------------------------------------+
|            Local Filesystem Persistence             |
|     JSON • Snapshots • ChromaDB • Sessions         |
+------------------------------------------------------+
```

---

## Architectural Responsibilities

| Layer           | Primary Responsibility            |
| --------------- | --------------------------------- |
| User Interface  | User interaction and presentation |
| Application API | External application contract     |
| Repository      | Repository understanding          |
| Indexing        | Semantic indexing                 |
| Retrieval       | Semantic search                   |
| Memory          | Persistent AI memory              |
| Editing         | Controlled file modification      |
| Persistence     | Local durable storage             |

---

# 2. High-Level Data Flow

The primary operational flow for Version 1 is shown below.

```text
Repository
    │
    ▼
Repository Scanner
    │
    ▼
Metadata Extraction
    │
    ▼
Document Loader
    │
    ▼
Repository Parser
    │
    ▼
Repository Chunker
    │
    ▼
RepositoryChunk
    │
    ▼
Embedding Provider (Ollama)
    │
    ▼
IndexedChunk
    │
    ▼
Chroma Vector Store
    │
    ▼
Semantic Retrieval
    │
    ▼
Retrieval Service
    │
    ▼
Application API
    │
    ▼
Frontend
```

This flow represents repository indexing and semantic retrieval.

Editing, memory, and future context assembly operate independently while consuming repository information through stable interfaces.

---

# 3. Backend Architecture

## Overview

The backend provides the application's domain logic, repository intelligence, AI integration, persistence management, and API surface.

Technology stack:

* FastAPI
* Pydantic v2

---

## Responsibilities

* Repository understanding
* Semantic indexing
* Semantic retrieval
* Local AI integration
* File editing orchestration
* Memory management
* API implementation
* Background task execution

---

## Ownership

The backend owns all business logic.

No frontend component performs repository reasoning.

---

## Inputs

* HTTP requests
* Repository files
* User prompts
* Background tasks

---

## Outputs

* API responses
* Streaming responses
* Edited files
* Persistent project state

---

## Dependencies

* Filesystem
* Ollama
* ChromaDB

---

## Explicit Non-Responsibilities

The backend does **not**:

* render user interfaces,
* manage frontend state,
* perform cloud synchronization.

---

# 4. Frontend Architecture

## Overview

The frontend provides the user-facing interface for interacting with Local OpenClaw.

Technology stack:

* React
* TypeScript
* Vite
* Zustand
* TanStack Query
* Monaco Editor

---

## Responsibilities

* User interaction
* Project management
* Chat interface
* Repository browsing
* Diff visualization
* Code editing
* API communication

---

## Ownership

The frontend owns presentation only.

---

## Inputs

* User actions
* Backend responses
* Streaming events

---

## Outputs

* HTTP requests
* UI updates

---

## Dependencies

* Backend API

---

## Explicit Non-Responsibilities

The frontend does **not**:

* parse repositories,
* generate embeddings,
* perform semantic search,
* modify repository state directly.

---

# 5. AI Stack

## Components

* Ollama
* nomic-embed-text
* Local chat model
* tiktoken

---

## Responsibilities

* Embedding generation
* Local inference
* Token estimation

---

## Ownership

The AI subsystem owns model interaction only.

Repository understanding remains independent.

---

## Inputs

* Repository chunks
* User queries

---

## Outputs

* Embeddings
* LLM responses

---

## Dependencies

* Ollama runtime

---

## Explicit Non-Responsibilities

The AI subsystem does **not**:

* scan repositories,
* manage persistence,
* perform retrieval logic,
* edit files directly.

---

# 6. Persistence Architecture

## Overview

Persistence is entirely local.

Version 1 intentionally avoids relational databases.

---

## Storage Types

Filesystem

```text
.local_openclaw/
```

Persistent JSON

ChromaDB vector persistence

---

## Responsibilities

* Project state
* Session state
* Memory persistence
* Snapshot storage
* Vector persistence

---

## Ownership

Persistence owns durable storage only.

---

## Inputs

Domain objects produced by higher-level subsystems.

---

## Outputs

Persistent state.

---

## Dependencies

Filesystem

ChromaDB

---

## Explicit Non-Responsibilities

Persistence does **not**:

* perform repository reasoning,
* execute AI inference,
* enforce business rules.

---

# 7. Repository Architecture

## Overview

The repository subsystem constructs a structured understanding of a software repository.

It is the foundational subsystem for all repository-aware functionality.

---

## Responsibilities

* Repository scanning
* Ignore rule handling
* Metadata extraction
* Document loading
* Language detection
* Parsing
* Chunk generation
* Deterministic chunk identifiers

---

## Ownership

Repository understanding.

---

## Inputs

Repository filesystem.

---

## Outputs

Repository domain models.

RepositoryChunk objects.

---

## Dependencies

Filesystem only.

---

## Explicit Non-Responsibilities

Repository architecture does **not**:

* generate embeddings,
* perform semantic retrieval,
* interact with language models,
* store vectors.

---

# 8. Indexing Architecture

## Overview

The indexing subsystem converts repository chunks into searchable semantic representations.

---

## Responsibilities

* Embedding generation
* IndexedChunk construction
* Vector persistence

---

## Ownership

Semantic indexing.

---

## Inputs

RepositoryChunk

---

## Outputs

IndexedChunk

Persistent vectors

---

## Dependencies

Repository subsystem

Embedding provider

Vector store

---

## Explicit Non-Responsibilities

Indexing does **not**:

* search vectors,
* assemble prompts,
* edit files,
* perform repository parsing.

---

# 9. Retrieval Architecture

## Overview

The retrieval subsystem performs semantic search over indexed repository content.

It provides repository-aware search while remaining independent of embedding generation.

---

## Responsibilities

* Query embedding generation
* Vector search orchestration
* Search result mapping

---

## Ownership

Semantic retrieval.

---

## Inputs

SearchQuery

---

## Outputs

SearchResponse

---

## Dependencies

EmbeddingProvider

VectorStore

---

## Explicit Non-Responsibilities

Retrieval does **not**:

* index repositories,
* own vector persistence,
* reconstruct repository state outside the retrieval projection,
* assemble prompts,
* interact with memory.

---

# 10. Memory Architecture

## Overview

The memory subsystem manages persistent conversational and architectural knowledge.

Version 1 establishes the architectural foundation without expanding memory capabilities beyond the defined scope.

---

## Responsibilities

* Facts memory
* Architecture memory
* Working context
* Session memory

---

## Ownership

Persistent AI memory.

---

## Inputs

Application state.

---

## Outputs

Memory records.

---

## Dependencies

Filesystem persistence.

---

## Explicit Non-Responsibilities

Memory does **not**:

* perform retrieval,
* parse repositories,
* edit files.

---

# 11. Editing Architecture

## Overview

The editing subsystem performs controlled source-code modification.

---

## Responsibilities

* Patch generation
* Diff preview
* Snapshot creation
* Rollback

---

## Ownership

Repository modification.

---

## Inputs

Approved edit operations.

---

## Outputs

Modified files.

Snapshots.

---

## Dependencies

Filesystem.

---

## Explicit Non-Responsibilities

Editing does **not**:

* understand repositories,
* generate embeddings,
* perform retrieval.

---

# 12. API Architecture

## Overview

The backend exposes a versioned REST API for all application functionality.

---

## Characteristics

* REST
* Versioned endpoints
* Server-Sent Events
* Background task support

---

## Responsibilities

* External application contract
* Request validation
* Response serialization
* Streaming

---

## Ownership

Application communication.

---

## Inputs

HTTP requests.

---

## Outputs

HTTP responses.

Streaming events.

---

## Dependencies

Backend services.

---

## Explicit Non-Responsibilities

The API layer does **not**:

* implement business logic,
* access persistence directly,
* perform repository reasoning.

---

# 13. Supported Languages

## Semantic Support

Current language-specific semantic parsing:

* Python

Python repositories receive AST-aware chunking.

---

## Generic Support

All text-based repositories receive generic line-based chunking.

---

## Architectural Extension

Support for additional languages is intended to be additive.

Existing subsystem boundaries and public interfaces should remain unchanged when introducing future language-specific parsers.

---

# Chapter Status

**Chapter 2 is complete and defines the permanent system architecture of Local OpenClaw.**

This chapter specifies subsystem responsibilities, ownership, dependencies, data flow, and architectural boundaries independently of the current Sprint 4 implementation state. It is intended to remain stable across future implementation work unless changed through a formal architecture decision.
