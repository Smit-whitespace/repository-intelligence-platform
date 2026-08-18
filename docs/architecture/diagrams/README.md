# Reusable Architecture Diagrams

> **Status:** Complete
> **Last Updated:** Sprint 13

---

This directory contains reusable Mermaid diagrams. Subsystem documentation references these by including them inline or linking to the pattern.

## How to Use

Copy the relevant diagram block into any `.md` file. Mermaid is rendered natively by GitHub.

## Available Diagrams

### System Architecture

```mermaid
graph TD
    UI["User Interface Layer<br/>React + TypeScript"] --> API["Application API Layer<br/>FastAPI + REST + SSE"]
    API --> PM["Project Management"]
    API --> REPO["Repository Understanding"]
    API --> CHAT["Chat"]
    API --> EDIT["Editing"]
    PM --> REPO
    PM --> INDEX["Indexing"]
    REPO --> INDEX
    INDEX --> RET["Retrieval"]
    RET --> CHAT
    CHAT --> CA["Context Assembly"]
    CHAT --> LLM["AI Provider (Ollama)"]
    EDIT --> SS["Snapshot Store"]
    INDEX --> VR["VectorStoreResolver"]
    RET --> VR
    VR --> VS["Vector Store (ChromaDB)"]
    PM --> FS["Filesystem"]
    EDIT --> FS
```

### Project Open Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant API
    participant PIS as ProjectInitializationService
    participant PS as ProjectService
    participant RS as RepositoryService
    participant IS as IndexingService

    User->>API: POST /projects/open
    API->>PIS: open_project(root_directory)
    PIS->>PS: open_project()
    PS-->>PIS: Project
    PIS->>RS: build_index()
    RS-->>PIS: RepositoryIndex
    PIS->>IS: index_repository()
    IS-->>PIS: IndexingResult
    PIS-->>API: Project
    API-->>User: OpenProjectResponse
```

### Repository Pipeline

```mermaid
graph LR
    FS["Filesystem"] --> SCAN["RepositoryScanner"]
    SCAN --> META["MetadataExtractor"]
    META --> LOAD["DocumentLoader"]
    LOAD --> CHUNK["RepositoryChunker"]
    CHUNK --> RC["RepositoryChunk"]
    RC --> IX["Indexing Service"]
```

### Indexing Pipeline

```mermaid
graph LR
    RC["RepositoryChunk"] --> IS["IndexingService"]
    IS --> IX["RepositoryIndexer"]
    IX --> EP["EmbeddingProvider (Ollama)"]
    IX --> VR["VectorStoreResolver"]
    VR --> VS["VectorStore (ChromaDB)"]
    EP --> EMB["EmbeddingVector"]
    EMB --> IC["IndexedChunk"]
    IC --> VS
    VS --> DB[("ChromaDB")]
```

### Retrieval Pipeline

```mermaid
graph LR
    CS["ChatService"] --> RS["RetrievalService"]
    RS --> EP["EmbeddingProvider"]
    RS --> VR["VectorStoreResolver"]
    VR --> VS2["VectorStore"]
    EP --> QEMB["Query Embedding"]
    VS2 --> DB2[("ChromaDB")]
    VS2 --> RESULTS["Search Results"]
    RESULTS --> HITS["SearchHit → SearchResult"]
    HITS --> CA["ContextAssembly"]
```

### Chat Pipeline

```mermaid
sequenceDiagram
    participant User
    participant CS as ChatService
    participant RS as RetrievalService
    participant CA as ContextAssembly
    participant LLM as ChatProvider

    User->>CS: chat(query, root_directory?)
    CS->>RS: search(query, root_directory?)
    RS-->>CS: SearchResponse
    CS->>CA: assemble(query, results)
    CA-->>CS: ContextAssemblyResponse (prompt)
    CS->>LLM: generate(prompt)
    LLM-->>CS: ChatResponse
    CS-->>User: ChatResponse
```

### Editing Pipeline

```mermaid
sequenceDiagram
    participant User
    participant ES as EditingService
    participant EP as EditingProvider
    participant CA as ChangeApplier
    participant SS as SnapshotStore

    User->>ES: edit(request)
    ES->>EP: edit(request)
    EP-->>ES: EditResponse (ChangeSet)
    ES-->>User: ChangeSet for review

    User->>ES: apply(change_set)
    ES->>ES: _create_snapshot()
    ES->>SS: save(snapshot)
    ES->>CA: apply(change_set)
    ES-->>User: snapshot_id

    User->>ES: rollback(snapshot_id)
    ES->>SS: load(snapshot_id)
    ES->>CA: restore(snapshot)
    ES-->>User: OK (204)
```

### Subsystem Dependencies

```mermaid
graph TD
    PM["Project Management"] --> REPO["Repository"]
    PM --> IDX["Indexing"]
    REPO --> IDX
    IDX --> RET["Retrieval"]
    RET --> CHAT["Chat"]
    CHAT --> CA["Context Assembly"]
    CHAT --> LLM["ChatProvider"]
    IDX --> VR["VectorStoreResolver"]
    RET --> VR
    VR --> VS["VectorStore"]
    PM --> STO["Storage"]
    EDIT["Editing"] --> STO
    EDIT --> LLM
    IDX --> EMB["EmbeddingProvider"]
    RET --> EMB
```

### Storage Relationships

```mermaid
graph LR
    PM["ProjectService"] --> SPR["StorageProvider"]
    SS["SnapshotStore"] --> SPR
    SPR --> FS[("Filesystem")]
    IX["RepositoryIndexer"] --> VR["VectorStoreResolver"]
    RS["RetrievalService"] --> VR
    VR --> VS3["VectorStore"]
    VS3 --> CDB[("ChromaDB")]
```

---

## Related

| Document | Link |
|----------|------|
| System Overview | [../system-overview.md](../system-overview.md) |
| Project Management | [../backend/project-management.md](../backend/project-management.md) |
| Repository | [../backend/repository.md](../backend/repository.md) |
| Indexing | [../backend/indexing.md](../backend/indexing.md) |
| Retrieval | [../backend/retrieval.md](../backend/retrieval.md) |
| Chat | [../backend/chat.md](../backend/chat.md) |
| Editing | [../backend/editing.md](../backend/editing.md) |
| Storage | [../backend/storage.md](../backend/storage.md) |
