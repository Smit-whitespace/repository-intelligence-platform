# Document 1 — Project Foundation

## Chapter 2 — System Architecture (Part A)

**Local OpenClaw (LOC)**
**Software Architecture Specification (SAS)**
**Document Status:** Authoritative
**Document:** 2 of 5 — Chapter 2 (Part A of IV)

---

# Chapter Metadata

| Property          | Value                                                                                    |
| ----------------- | ---------------------------------------------------------------------------------------- |
| **Document**      | Project Foundation                                                                       |
| **Chapter**       | Chapter 2 — System Architecture                                                          |
| **Scope**         | Permanent Architecture                                                                   |
| **Stability**     | Frozen (subject only to future ADRs)                                                     |
| **Depends On**    | Document 0 — Project Manifest, Document 1 — Chapter 1                                    |
| **Referenced By** | Document 2 — Engineering State, Document 3 — Release State, Implementation Documentation |
| **Last Updated**  | Sprint 4 RC-4                                                                            |

---

# 1. Overall System Architecture

## 1.1 Architectural Overview

Local OpenClaw (LOC) follows a **modular layered architecture** built around **explicit subsystem ownership** and **stable public interfaces**. Every major capability is encapsulated within a dedicated subsystem that owns a narrowly defined responsibility and communicates with other subsystems exclusively through published contracts.

Rather than organizing the system around technologies or frameworks, the architecture is organized around **domain responsibilities**. This allows implementation technologies to evolve over time while preserving the overall structure of the system.

The architectural layering is intentionally conservative:

* higher layers coordinate user interaction,
* middle layers implement repository intelligence,
* lower layers provide durable persistence,
* cross-cutting concerns remain independent of business logic.

This organization minimizes coupling, encourages high cohesion, and supports incremental evolution without requiring architectural redesign.

The architecture is designed to remain valid beyond Version 1. Future capabilities should extend existing subsystem boundaries rather than introducing parallel architectures or overlapping responsibilities.

---

## 1.2 Architectural Characteristics

Local OpenClaw is intentionally designed as:

* Offline-first
* Repository-centric
* Modular
* Layered
* Deterministic
* Repository-aware
* AI-assisted
* Filesystem-based
* Incrementally extensible
* Interface-driven

These characteristics describe the permanent architecture rather than any particular implementation.

---

## 1.3 Architectural Layers

```text
+-------------------------------------------------------------+
|                    User Interface Layer                     |
|         React • Monaco • Zustand • TanStack Query          |
+-------------------------------------------------------------+
                           │
                           ▼
+-------------------------------------------------------------+
|                    Application API Layer                    |
|          FastAPI • REST • SSE • Background Tasks           |
+-------------------------------------------------------------+
                           │
                           ▼
+-------------------------------------------------------------+
|                  Domain Service Layer                       |
| Repository │ Indexing │ Retrieval │ Memory │ Editing        |
+-------------------------------------------------------------+
                           │
                           ▼
+-------------------------------------------------------------+
|                  Infrastructure Layer                       |
|      Ollama │ ChromaDB │ Filesystem │ Configuration         |
+-------------------------------------------------------------+
```

The architectural layers define **dependency direction**, not deployment boundaries.

Multiple architectural subsystems may execute within the same backend process while remaining logically independent.

---

# 2. Architecture Principles

The following principles govern every architectural decision within Local OpenClaw.

These principles are intended to remain stable across future releases and should guide implementation whenever multiple technically correct solutions exist.

---

## 2.1 Offline-First

The system is designed to operate entirely on the local machine.

Repository understanding, semantic indexing, retrieval, editing, and AI interaction should not require continuous cloud connectivity.

This preserves privacy, improves responsiveness, and reduces external dependencies.

---

## 2.2 Explicit Subsystem Ownership

Every subsystem owns a clearly defined responsibility.

Responsibilities should not overlap.

Whenever ownership is ambiguous, the architecture should be clarified rather than allowing multiple subsystems to implement similar behavior.

---

## 2.3 Stable Public Interfaces

Subsystems communicate only through stable public contracts.

Internal implementation models remain private to their owning subsystem.

Stable interfaces reduce coupling and allow implementations to evolve independently.

---

## 2.4 High Cohesion

Each subsystem should group closely related responsibilities.

Responsibilities that naturally belong together should remain together.

Subsystems should avoid becoming collections of unrelated functionality.

---

## 2.5 Low Coupling

Subsystems should depend only on the minimum information required to fulfill their responsibilities.

Implementation details must not leak across subsystem boundaries.

Reducing coupling simplifies testing, maintenance, and future evolution.

---

## 2.6 Composition over Inheritance

Behavior should be assembled by composing independent components rather than constructing deep inheritance hierarchies.

Composition produces clearer ownership and reduces long-term maintenance complexity.

---

## 2.7 Local AI Execution

AI capabilities are treated as local infrastructure.

Repository understanding should remain independent of any particular language model implementation.

This separation allows AI providers to evolve without altering repository architecture.

---

## 2.8 Deterministic Repository Processing

Repository scanning, parsing, chunk generation, indexing, and editing should behave deterministically whenever practical.

Deterministic behavior improves reproducibility, debugging, testing, and user trust.

---

## 2.9 Explicit Data Flow

Information should move through clearly defined architectural stages.

Data transformations should occur within the subsystem responsible for that transformation.

Implicit processing pipelines should be avoided.

---

## 2.10 Minimal Trusted Boundaries

Only the minimum number of architectural components should require direct access to infrastructure such as:

* filesystem operations,
* vector persistence,
* AI providers,
* external libraries.

Reducing trusted boundaries improves maintainability and limits unintended coupling.

---

# 3. Dependency Direction Rules

## 3.1 Dependency Hierarchy

Architectural dependencies flow downward through the system.

```text
Frontend
    │
    ▼
Application API
    │
    ▼
Repository Services
Indexing Services
Retrieval Services
Memory Services
Editing Services
    │
    ▼
Infrastructure
(Filesystem • Ollama • ChromaDB)
```

This diagram defines the permitted direction of architectural dependencies rather than runtime execution order.

---

## 3.2 Dependency Rules

The following rules apply throughout the project.

### Rule 1

Dependencies must always point downward.

Higher layers may depend on lower layers.

Lower layers must never depend on higher layers.

---

### Rule 2

Peer subsystems communicate only through stable public interfaces.

Internal implementation details remain private.

---

### Rule 3

Subsystems must not directly access another subsystem's internal models.

Only published contracts may cross subsystem boundaries.

---

### Rule 4

Infrastructure components never own business logic.

Infrastructure provides capabilities.

Domain subsystems define behavior.

---

### Rule 5

Technology choices must not alter dependency direction.

Replacing an implementation technology must not require architectural restructuring.

---

# 4. Architectural Views

This chapter presents multiple architectural views of the same system.

Each view emphasizes a different aspect of the architecture.

| View                | Purpose                                                        |
| ------------------- | -------------------------------------------------------------- |
| **Layer View**      | Overall organization of the system.                            |
| **Subsystem View**  | Responsibilities and ownership of each subsystem.              |
| **Dependency View** | Permitted architectural dependencies.                          |
| **Workflow View**   | Movement of information through major architectural use cases. |

These views are complementary.

They describe the same architecture from different perspectives and should not be interpreted as separate architectures.

---

# 5. High-Level Data Flow

The following workflows illustrate the two primary architectural use cases established in Version 1.

They describe the movement of information between architectural subsystems rather than implementation details.

---

## 5.1 Repository Indexing Flow

The repository indexing workflow transforms repository source files into semantically searchable vector representations.

```text
Repository
    │
    ▼
Repository Scanner
    │
    ▼
Metadata Extractor
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
Embedding Provider
    │
    ▼
IndexedChunk
    │
    ▼
ChromaDB Vector Store
```

The indexing workflow terminates when repository content has been persisted in the vector store.

Subsequent retrieval operations operate independently of repository scanning.

---

## 5.2 Semantic Retrieval Flow

The semantic retrieval workflow transforms a user query into repository-aware search results.

```text
User Query
    │
    ▼
Retrieval Service
    │
    ▼
Embedding Provider
    │
    ▼
VectorStore
    │
    ▼
ChromaDB
    │
    ▼
SearchHit
    │
    ▼
SearchResponse
    │
    ▼
Application API
    │
    ▼
Frontend
```

Retrieval operates exclusively on indexed repository information.

It does not modify repository state, generate embeddings for repository content, or perform repository parsing.

---

## Part A Status

This part establishes the **structural architecture** of Local OpenClaw by defining:

* Overall architectural organization
* Architecture principles
* Dependency direction rules
* Architectural views
* High-level indexing workflow
* High-level retrieval workflow

Subsequent parts define the responsibilities and boundaries of each individual subsystem while remaining consistent with the architectural principles established here.

# Document 1 — Project Foundation

## Chapter 2 — System Architecture (Part B)

**Local OpenClaw (LOC)**
**Software Architecture Specification (SAS)**
**Document Status:** Authoritative
**Document:** 2 of 5 — Chapter 2 (Part B of IV)

---

# 6. Backend Architecture

## 6.1 Overview

The backend constitutes the application's execution core. It implements the domain behavior of Local OpenClaw by coordinating repository understanding, semantic indexing, semantic retrieval, memory management, editing operations, persistence, and external API exposure.

The backend is organized around **domain-oriented subsystems**, not around frameworks or infrastructure libraries. Each subsystem owns a distinct responsibility and communicates with other subsystems only through stable public interfaces.

---

## 6.2 Architectural Responsibility

The backend is responsible for:

* implementing domain behavior,
* orchestrating repository workflows,
* exposing application capabilities through the API,
* coordinating AI infrastructure,
* managing persistent project state,
* enforcing subsystem boundaries.

It is the authoritative owner of application logic.

---

## 6.3 Reference Implementation (Version 1)

Current implementation technologies:

* FastAPI
* Pydantic v2
* Python 3.12
* Uvicorn

These technologies are implementation choices rather than architectural requirements.

---

## 6.4 Responsibilities

The backend owns:

* repository scanning orchestration,
* metadata extraction orchestration,
* document loading,
* parsing coordination,
* chunk generation,
* semantic indexing,
* semantic retrieval,
* memory coordination,
* editing coordination,
* persistence coordination,
* request handling,
* response generation,
* streaming communication,
* background task execution.

---

## 6.5 Ownership

The backend exclusively owns business logic.

No business rules are implemented within the frontend or infrastructure components.

---

## 6.6 Inputs

The backend consumes:

* HTTP requests,
* Server-Sent Event connections,
* repository filesystem content,
* user prompts,
* editing requests,
* background jobs.

---

## 6.7 Outputs

The backend produces:

* REST responses,
* streaming responses,
* repository modifications,
* semantic search results,
* persistent project state,
* task status information.

---

## 6.8 Dependencies

The backend depends on:

* local filesystem,
* Ollama,
* ChromaDB,
* application configuration.

Dependencies are accessed through subsystem-owned abstractions wherever practical.

---

## 6.9 Explicit Non-Responsibilities

The backend does **not**:

* render user interfaces,
* own frontend state,
* implement IDE functionality,
* manage cloud infrastructure,
* synchronize repositories across devices.

---

# 7. Frontend Architecture

## 7.1 Overview

The frontend provides the user-facing interaction layer of Local OpenClaw.

Its purpose is to present repository information, AI interactions, editing workflows, and application state while delegating all repository intelligence and business logic to the backend.

---

## 7.2 Architectural Responsibility

The frontend owns:

* presentation,
* interaction,
* visualization,
* client-side state,
* user workflows.

The frontend is intentionally thin with respect to domain behavior.

---

## 7.3 Reference Implementation (Version 1)

Current implementation technologies:

* React
* TypeScript
* Vite
* Zustand
* TanStack Query
* Monaco Editor

These technologies may evolve without affecting architectural responsibilities.

---

## 7.4 Responsibilities

The frontend is responsible for:

* project selection,
* repository browsing,
* conversational interface,
* editor presentation,
* diff visualization,
* rollback interaction,
* task visualization,
* API communication,
* streaming updates.

---

## 7.5 Ownership

The frontend owns only presentation logic.

It never becomes the authoritative owner of repository state.

---

## 7.6 Inputs

The frontend consumes:

* user actions,
* REST responses,
* streaming events,
* task updates.

---

## 7.7 Outputs

The frontend produces:

* API requests,
* editing requests,
* indexing requests,
* retrieval requests,
* user interface updates.

---

## 7.8 Dependencies

The frontend depends solely on the public backend API.

No frontend component directly depends upon repository, indexing, retrieval, or persistence implementations.

---

## 7.9 Explicit Non-Responsibilities

The frontend does **not**:

* scan repositories,
* parse files,
* generate embeddings,
* perform semantic retrieval,
* modify repositories directly,
* access persistence.

---

# 8. AI Stack

## 8.1 Overview

The AI subsystem provides the machine learning capabilities required by Local OpenClaw while remaining independent from repository understanding.

The architecture intentionally separates AI infrastructure from repository intelligence so that models may evolve without affecting higher-level domain behavior.

---

## 8.2 Architectural Responsibility

The AI subsystem is responsible for:

* embedding generation,
* local language model inference,
* token estimation,
* model interaction.

It provides AI capabilities as infrastructure to the rest of the system.

---

## 8.3 Reference Implementation (Version 1)

Current implementation technologies:

* Ollama
* nomic-embed-text
* Local chat model (configured through application settings)
* tiktoken

The architecture depends only on the capabilities provided by these technologies, not on their specific implementations.

---

## 8.4 Responsibilities

The AI subsystem owns:

* embedding generation,
* inference requests,
* token counting,
* model communication.

---

## 8.5 Ownership

The AI subsystem owns interaction with language models.

It does **not** own repository understanding.

---

## 8.6 Inputs

The AI subsystem consumes:

* repository chunk content,
* retrieval queries,
* conversational prompts.

---

## 8.7 Outputs

The AI subsystem produces:

* embeddings,
* language model responses,
* token information.

---

## 8.8 Dependencies

The subsystem depends on:

* local model runtime,
* configured models.

---

## 8.9 Explicit Non-Responsibilities

The AI subsystem does **not**:

* scan repositories,
* determine repository structure,
* manage persistence,
* perform semantic search,
* edit repositories,
* manage memory.

---

# 9. Persistence Architecture

## 9.1 Overview

The persistence subsystem provides durable local storage for application state.

It is intentionally separated from business logic so that storage mechanisms remain replaceable without affecting higher-level architectural responsibilities.

Version 1 adopts a filesystem-first persistence strategy to minimize operational complexity while supporting the project's offline-first objectives.

---

## 9.2 Architectural Responsibility

The persistence subsystem owns:

* durable storage,
* persistence lifecycle,
* storage organization,
* snapshot durability,
* vector persistence.

It stores information produced by higher-level subsystems but never determines how that information should be interpreted.

---

## 9.3 Reference Implementation (Version 1)

Current persistence technologies:

* Local filesystem
* JSON documents
* ChromaDB persistent collections

No relational database is required for Version 1.

---

## 9.4 Responsibilities

The persistence subsystem is responsible for:

* project storage,
* session storage,
* snapshot storage,
* vector persistence,
* memory persistence,
* configuration persistence.

---

## 9.5 Ownership

The persistence subsystem owns durable storage mechanisms and data lifecycle operations.

It does **not** own domain behavior, business rules, repository intelligence, or application workflows.

---

## 9.6 Inputs

The persistence subsystem consumes domain objects generated by:

* Repository
* Indexing
* Retrieval (where persistence is explicitly required)
* Memory
* Editing
* Configuration

---

## 9.7 Outputs

The persistence subsystem provides:

* durable project state,
* persistent vector collections,
* session information,
* snapshots,
* stored memory.

---

## 9.8 Dependencies

The persistence subsystem depends on:

* local filesystem,
* ChromaDB.

It has no dependency on higher-level business logic.

---

## 9.9 Explicit Non-Responsibilities

The persistence subsystem does **not**:

* scan repositories,
* generate embeddings,
* perform retrieval,
* edit files,
* implement business rules,
* expose APIs,
* interpret domain semantics.

---

## Part B Status

This part defines the permanent architecture of the infrastructure-facing subsystems:

* Backend
* Frontend
* AI Stack
* Persistence

Each subsystem is specified in terms of its architectural responsibility, ownership, dependencies, and boundaries while distinguishing permanent architectural intent from the Version 1 reference implementation.



# Document 1 — Project Foundation

## Chapter 2 — System Architecture (Part C)

**Local OpenClaw (LOC)**
**Software Architecture Specification (SAS)**
**Document Status:** Authoritative
**Document:** 2 of 5 — Chapter 2 (Part C of IV)

---

# 10. Repository Architecture

## 10.1 Overview

The Repository subsystem is the architectural foundation of Local OpenClaw.

It is responsible for constructing a structured, deterministic representation of a software repository that can be consumed by higher-level subsystems. Every repository-aware capability ultimately depends on this subsystem.

The Repository subsystem understands **repository structure**, not repository meaning. Semantic interpretation begins only after repository content has been transformed into repository chunks.

---

## 10.2 Architectural Responsibility

The Repository subsystem owns the complete lifecycle of repository understanding prior to semantic indexing.

Its responsibilities include:

* repository discovery,
* filesystem traversal,
* ignore rule application,
* metadata extraction,
* document loading,
* language-aware parsing,
* repository chunk generation,
* deterministic chunk identification.

It is the canonical producer of repository domain models.

---

## 10.3 Reference Implementation (Version 1)

Current implementation consists of:

* Repository Scanner
* Repository Metadata Extractor
* Repository Document Loader
* Repository Parser
* Generic Line Chunker
* Python AST Chunker
* Deterministic Chunk ID Generator

The architecture does not depend on these specific implementations, only on the capabilities they provide.

---

## 10.4 Responsibilities

The Repository subsystem is responsible for:

* discovering repository contents,
* applying repository ignore rules,
* determining repository metadata,
* loading textual documents,
* identifying supported languages,
* constructing repository domain models,
* generating deterministic repository chunks,
* producing repository chunk identifiers.

---

## 10.5 Ownership

The Repository subsystem is the exclusive owner of repository structure.

Every subsystem requiring repository information obtains it through Repository-owned models.

---

## 10.6 Inputs

The Repository subsystem consumes:

* repository filesystem,
* repository configuration,
* ignore rules.

---

## 10.7 Outputs

The Repository subsystem produces:

* RepositoryEntry
* RepositoryDocument
* RepositoryChunk
* Repository metadata
* Chunk boundaries
* Deterministic chunk identifiers

These outputs form the canonical repository representation consumed by downstream subsystems.

---

## 10.8 Dependencies

The Repository subsystem depends only upon:

* local filesystem,
* language parsers,
* repository configuration.

It deliberately avoids dependencies on:

* AI infrastructure,
* vector storage,
* retrieval,
* memory,
* editing.

---

## 10.9 Explicit Non-Responsibilities

The Repository subsystem does **not**:

* generate embeddings,
* perform semantic indexing,
* perform semantic retrieval,
* communicate with language models,
* store vectors,
* manage conversational memory,
* modify repository contents.

---

# 11. Indexing Architecture

## 11.1 Overview

The Indexing subsystem transforms repository content into semantic representations suitable for similarity search.

It bridges repository understanding and semantic retrieval while remaining independent of retrieval workflows.

---

## 11.2 Architectural Responsibility

The Indexing subsystem owns:

* embedding generation,
* semantic indexing,
* construction of indexing models,
* persistence of vector representations.

It is the only subsystem that understands embeddings.

---

## 11.3 Reference Implementation (Version 1)

Current implementation consists of:

* RepositoryIndexer
* EmbeddingProvider
* OllamaProvider
* ChromaVectorStore

---

## 11.4 Responsibilities

The Indexing subsystem is responsible for:

* converting RepositoryChunk into embeddings,
* constructing indexing models,
* validating embedding generation,
* persisting vectors,
* coordinating vector storage.

---

## 11.5 Ownership

The Indexing subsystem is the exclusive owner of semantic indexing.

Embedding-aware implementation models remain private to this subsystem.

---

## 11.6 Inputs

The Indexing subsystem consumes:

* RepositoryChunk
* embedding requests
* embedding provider responses

---

## 11.7 Outputs

The Indexing subsystem produces:

* IndexedChunk
* persisted vector representations

These outputs exist solely to support semantic retrieval.

---

## 11.8 Dependencies

The Indexing subsystem depends upon:

* Repository subsystem
* EmbeddingProvider
* VectorStore

It does not depend upon Retrieval, Memory, or Editing.

---

## 11.9 Explicit Non-Responsibilities

The Indexing subsystem does **not**:

* execute searches,
* construct retrieval responses,
* assemble prompts,
* understand conversational context,
* edit repository contents.

---

# 12. Retrieval Architecture

## 12.1 Overview

The Retrieval subsystem provides semantic access to indexed repository knowledge.

It transforms user search requests into repository-aware search results while remaining independent from repository indexing and persistence implementation details.

Retrieval operates exclusively on indexed information and never modifies repository state.

---

## 12.2 Architectural Responsibility

The Retrieval subsystem owns:

* query embedding generation,
* semantic search orchestration,
* retrieval result projection,
* search response construction.

It is responsible for exposing repository search capabilities through stable retrieval models.

---

## 12.3 Reference Implementation (Version 1)

Current implementation consists of:

* RetrievalService
* SearchQuery
* SearchHit
* SearchResult
* SearchResponse

The Retrieval subsystem interacts with semantic storage exclusively through the `VectorStore` abstraction.

---

## 12.4 Responsibilities

The Retrieval subsystem is responsible for:

* embedding search queries,
* delegating semantic search,
* transforming search projections,
* constructing retrieval responses.

---

## 12.5 Ownership

The Retrieval subsystem is the exclusive owner of semantic retrieval behavior.

It owns retrieval-facing models but does not own semantic persistence.

---

## 12.6 Inputs

The Retrieval subsystem consumes:

* SearchQuery
* EmbeddingProvider
* VectorStore

---

## 12.7 Outputs

The Retrieval subsystem produces:

* SearchHit
* SearchResult
* SearchResponse

These models represent the public retrieval contract.

---

## 12.8 Dependencies

The Retrieval subsystem depends upon:

* EmbeddingProvider
* VectorStore

It intentionally does not depend directly upon:

* Repository subsystem,
* Indexing implementation models,
* ChromaDB,
* persistence mechanisms.

---

## 12.9 Explicit Non-Responsibilities

The Retrieval subsystem does **not**:

* scan repositories,
* generate repository chunks,
* generate repository embeddings,
* persist vectors,
* edit repositories,
* manage memory,
* assemble LLM prompts.

---

# 13. Memory Architecture

## 13.1 Overview

The Memory subsystem defines the architectural foundation for persistent conversational and project knowledge.

It provides long-term contextual storage that enables future repository-aware interactions while remaining independent of repository indexing and semantic retrieval.

The subsystem is architecturally defined as part of Version 1.

Sprint 4 establishes its architectural boundaries while implementation is intentionally deferred beyond the current sprint.

---

## 13.2 Architectural Responsibility

The Memory subsystem owns:

* persistent facts,
* architectural memory,
* working context,
* session context.

It provides structured memory capabilities to higher-level application workflows.

---

## 13.3 Reference Implementation (Version 1)

The architectural design is frozen.

Implementation beyond subsystem boundaries is deferred until a future sprint.

---

## 13.4 Responsibilities

The Memory subsystem is responsible for:

* storing persistent knowledge,
* retrieving stored knowledge,
* maintaining session context,
* maintaining working context,
* supporting future contextual reasoning.

---

## 13.5 Ownership

The Memory subsystem is the exclusive owner of conversational and architectural memory.

---

## 13.6 Inputs

The Memory subsystem consumes:

* application events,
* conversation state,
* approved memory updates.

---

## 13.7 Outputs

The Memory subsystem produces:

* persistent memory records,
* working context,
* architectural memory,
* session memory.

---

## 13.8 Dependencies

The Memory subsystem depends upon:

* persistence,
* configuration.

It remains independent of repository indexing and retrieval implementation.

---

## 13.9 Explicit Non-Responsibilities

The Memory subsystem does **not**:

* scan repositories,
* generate embeddings,
* execute semantic retrieval,
* edit repositories,
* expose APIs.

---

# 14. Editing Architecture

## 14.1 Overview

The Editing subsystem provides controlled modification of repository contents.

Every editing operation is designed to be transparent, reviewable, and reversible.

The subsystem emphasizes safety over automation.

---

## 14.2 Architectural Responsibility

The Editing subsystem owns:

* patch application,
* diff generation,
* snapshot creation,
* rollback,
* controlled repository modification.

---

## 14.3 Reference Implementation (Version 1)

Current implementation targets include:

* patch-based editing,
* snapshot generation,
* diff preview,
* rollback support.

---

## 14.4 Responsibilities

The Editing subsystem is responsible for:

* applying approved modifications,
* generating diffs,
* creating recovery snapshots,
* restoring previous repository states.

---

## 14.5 Ownership

The Editing subsystem is the exclusive owner of repository modification.

No other subsystem performs direct source-code editing.

---

## 14.6 Inputs

The Editing subsystem consumes:

* approved edit operations,
* repository files,
* snapshot requests.

---

## 14.7 Outputs

The Editing subsystem produces:

* modified repository files,
* diff previews,
* snapshots,
* rollback results.

---

## 14.8 Dependencies

The Editing subsystem depends upon:

* Repository subsystem,
* Persistence subsystem,
* local filesystem.

---

## 14.9 Explicit Non-Responsibilities

The Editing subsystem does **not**:

* understand repository semantics,
* perform semantic retrieval,
* generate embeddings,
* manage memory,
* implement conversational workflows.

---

## Part C Status

This part defines the permanent architecture of the domain-oriented subsystems:

* Repository
* Indexing
* Retrieval
* Memory
* Editing

Each subsystem is specified in terms of its architectural responsibility, ownership, boundaries, dependencies, and public role within the overall system architecture. Together, these definitions establish the core domain model of Local OpenClaw while remaining independent of implementation progress and specific technologies.


Document 1 — Project Foundation
Chapter 2 — System Architecture (Part D)

Local OpenClaw (LOC)
Software Architecture Specification (SAS)
Document Status: Authoritative
Document: 2 of 5 — Chapter 2 (Part D of IV)

15. API Architecture
15.1 Overview

The API subsystem provides the external application boundary of Local OpenClaw.

It exposes the capabilities of the backend through stable, versioned interfaces while ensuring that all domain behavior remains within the owning subsystems.

The API is intentionally thin. It coordinates requests, delegates work to the appropriate subsystem, and returns structured responses without implementing business logic.

15.2 Architectural Responsibility

The API subsystem is responsible for:

exposing application capabilities,
validating incoming requests,
routing requests to domain services,
serializing responses,
streaming long-running operations,
exposing task status,
maintaining API version compatibility.

It defines the contract between the frontend and backend.

15.3 Reference Implementation (Version 1)

Version 1 exposes:

Versioned REST endpoints (/api/v1)
Server-Sent Events (SSE) for streaming
Background task APIs
Standardized error responses

These implementation choices realize the architectural responsibility without defining it.

15.4 Responsibilities

The API subsystem owns:

request validation,
response serialization,
endpoint organization,
API versioning,
streaming communication,
background task coordination,
standardized error responses.
15.5 Ownership

The API subsystem is the exclusive owner of external application contracts.

No domain subsystem exposes transport protocols directly.

15.6 Inputs

The API subsystem consumes:

HTTP requests,
streaming connections,
background task requests.
15.7 Outputs

The API subsystem produces:

REST responses,
streaming events,
task identifiers,
task status responses,
standardized error objects.
15.8 Dependencies

The API subsystem depends upon:

Backend services,
Configuration,
Validation infrastructure.

It does not directly depend upon infrastructure implementations such as ChromaDB or Ollama.

15.9 Explicit Non-Responsibilities

The API subsystem does not:

implement business rules,
scan repositories,
generate embeddings,
perform semantic retrieval,
manage memory,
edit repositories,
persist application state.
16. Cross-Cutting Concerns

Certain architectural responsibilities span multiple subsystems without belonging exclusively to any single one. These concerns provide consistency across the application while remaining independent of domain behavior.

16.1 Configuration

Configuration centralizes application settings required by multiple subsystems.

Responsibilities include:

application configuration,
AI configuration,
persistence configuration,
server configuration,
feature configuration.

Configuration defines operational behavior but never business logic.

16.2 Validation

Validation ensures that information entering subsystem boundaries satisfies the expected contracts.

Validation occurs:

at API boundaries,
between public interfaces,
during model construction,
before persistence operations where appropriate.

Validation failures should be detected as early as practical.

16.3 Logging

Logging provides operational visibility into system behavior.

Logging is intended to support:

diagnostics,
troubleshooting,
operational monitoring,
future observability.

Logging remains an implementation concern and should not influence business logic.

16.4 Error Propagation

Subsystems report failures through well-defined interfaces.

Each subsystem owns its own implementation-specific errors while exposing stable error behavior to higher architectural layers.

Errors should propagate upward through subsystem boundaries rather than bypassing architectural layers.

16.5 Background Execution

Operations with potentially significant execution time may execute asynchronously.

Examples include:

repository indexing,
large editing operations,
future long-running maintenance tasks.

Background execution is an application capability rather than a subsystem.

16.6 Observability

The architecture is designed to support future operational visibility without coupling monitoring concerns to business logic.

Potential observability capabilities include:

structured logging,
execution metrics,
subsystem health monitoring,
task execution monitoring.

These concerns remain independent of domain responsibilities.

17. Architectural Extension Philosophy

The Local OpenClaw architecture is intentionally evolutionary rather than revolutionary.

Future capabilities should extend existing subsystem responsibilities instead of introducing competing architectures or overlapping ownership.

Architectural growth should occur by:

extending existing public interfaces,
introducing additional implementations behind stable abstractions,
expanding subsystem capabilities while preserving ownership boundaries,
introducing new abstractions only when justified by multiple concrete implementations.

The preferred order of architectural evolution is:

Extend an existing subsystem.
Extend an existing public interface.
Introduce a new implementation behind an existing abstraction.
Introduce a new abstraction only when repeated implementation patterns demonstrate a clear need.

Architectural simplicity is preferred over premature extensibility.

18. Architectural Invariants

The following architectural invariants are intended to remain true throughout the lifetime of the project unless explicitly modified by an accepted Architecture Decision Record (ADR).

18.1 Repository Ownership

The Repository subsystem is the canonical source of repository information.

Repository structure originates exclusively within this subsystem.

18.2 Repository Domain Models

Repository domain models represent repository information independently of indexing, retrieval, memory, or editing concerns.

They form the canonical representation of repository content.

18.3 Embedding Ownership

Embedding-aware models remain internal implementation models of the Indexing subsystem.

Embeddings are an implementation detail of semantic indexing and do not cross subsystem boundaries.

18.4 Retrieval Projection

The Retrieval subsystem exposes retrieval projections rather than indexing implementation models.

Retrieval contracts are independent of vector persistence implementation.

18.5 Persistence Responsibility

Persistence stores durable application state but owns no business logic.

Interpretation of persisted information always belongs to higher-level subsystems.

18.6 API Responsibility

The API subsystem exposes application capabilities without implementing domain behavior.

Business logic remains entirely within domain subsystems.

18.7 Exclusive Subsystem Ownership

Every architectural responsibility has exactly one owning subsystem.

Ownership overlap is considered an architectural defect.

18.8 Stable Public Interfaces

Subsystem communication occurs exclusively through stable public interfaces.

Internal implementation details remain private to the owning subsystem.

18.9 Explicit Dependency Direction

Architectural dependencies always follow the documented dependency hierarchy.

Lower layers never depend upon higher layers.

18.10 Deterministic Repository Processing

Repository understanding should remain deterministic wherever practical.

Equivalent repository states should produce equivalent repository representations.

19. Supported Languages

The architecture is language-aware but language-independent.

Repository understanding is designed to support multiple programming and markup languages while allowing language-specific implementations to evolve independently.

Version 1 Language Support

Version 1 provides architectural support for:

Python
Plain Text
Markdown
JSON
YAML
TOML

Python receives enhanced structural understanding through Abstract Syntax Tree (AST)-aware chunking.

Other textual formats are processed using deterministic line-based chunking.

Future language support should extend the Repository subsystem without affecting higher-level architectural responsibilities.

20. Chapter Summary

This chapter defines the permanent architectural structure of Local OpenClaw.

It establishes:

the overall layered architecture,
architectural principles,
subsystem responsibilities,
ownership boundaries,
dependency direction,
repository indexing workflow,
semantic retrieval workflow,
cross-cutting architectural concerns,
extension philosophy,
architectural invariants,
supported language strategy.

Collectively, these sections define how the system is architected, independent of implementation progress or release status.

This chapter is intended to remain stable over the lifetime of the project. Changes to the architecture described herein should occur only through an accepted Architecture Decision Record (ADR).