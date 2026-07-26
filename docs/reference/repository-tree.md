# Repository Tree

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Backend

```
backend/
    app/
        api/
            routes/
                chat.py             # Chat endpoints
                editing.py          # Editing endpoints
                editing_schemas.py  # Editing request/response schemas
                health.py           # Health check endpoint
                models.py           # Shared API models
                projects.py         # Project management endpoints
                repository.py       # Repository endpoints
                system.py           # System status endpoints
            __init__.py
            exception_handlers.py
            response_docs.py        # Reusable OpenAPI response docs
            router.py               # Main API router
            schemas.py              # Shared API schemas
        chat/
            models.py               # Chat domain models
            ollama_provider.py      # Ollama chat provider implementation
            providers.py            # ChatProvider interface
            schemas.py              # Chat API schemas
            service.py              # Chat orchestration
        context_assembly/
            models.py               # Context assembly models
            providers.py            # ContextAssembly interface
            service.py              # Default context assembly implementation
        core/
            config/
                models.py           # Configuration models
                provider.py         # Configuration loading
                settings.py         # Application settings
            logging/
                configuration.py    # Logging config
                constants.py        # Logging constants
                factory.py          # Logger factory
            storage/
                abstractions.py     # StorageProvider interface
                exceptions.py       # Storage exceptions
                filesystem.py       # Filesystem storage implementation
                models.py           # Storage models
        dependencies/
            providers.py            # Dependency injection providers
        editing/
            change_applier.py       # File modification engine
            default_provider.py     # Default editing provider
            exceptions.py           # Editing exceptions
            models.py               # Editing domain models
            providers.py            # EditingProvider interface
            service.py              # Editing orchestration
            snapshot_models.py      # Snapshot models
            snapshot_store.py       # Snapshot persistence
        indexing/
            chroma_store.py         # ChromaDB vector store adapter
            exceptions.py           # Indexing exceptions
            indexer.py              # Repository indexer
            models.py               # Indexing domain models
            ollama_provider.py      # Ollama embedding provider
            providers.py            # EmbeddingProvider interface
            retrieval_models.py     # Retrieval domain models
            retrieval_service.py    # Retrieval orchestration
            service.py              # Indexing orchestration
            stores.py               # VectorStore interface
        main.py                     # Application entry point
        projects/
            exceptions.py           # Project exceptions
            initialization_service.py # Project initialization orchestration
            models.py               # Project domain model
            repository.py           # Project persistence
            schemas.py              # Project API schemas
            service.py              # Project lifecycle service
        repository/
            chunk_ids.py            # Deterministic chunk ID generation
            chunking_algorithms.py  # Chunking algorithm interface + line impl
            chunking.py             # Chunk routing and chunk building
            documents.py            # Document loading
            embeddings.py           # Embedding utilities
            exceptions.py           # Repository exceptions
            filetypes.py            # File type detection
            hashing.py              # SHA-256 hashing
            ignore.py               # Ignore rule handling
            languages.py            # Language detection
            manifest.py             # Repository manifest builder
            metadata.py             # Fast and slow metadata extraction
            mime.py                 # MIME type detection
            models.py               # Repository domain models
            python_ast_algorithm.py # Python AST chunking
            python_parser.py        # Python parser
            scanner.py              # Directory traversal
            schemas.py              # Repository API schemas
            service.py              # Repository public API
```

## Frontend

```
frontend/
    (React + TypeScript + Vite)
```

## Tests

```
backend/tests/
    api/                            # API endpoint tests
    indexing/                       # Indexing service tests
    projects/                       # Project service tests
    repository/                     # Repository tests
    editing/                        # Editing service tests
    chat/                           # Chat service tests
    context_assembly/               # Context assembly tests
```
