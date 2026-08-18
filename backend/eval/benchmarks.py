"""Golden repository evaluation benchmarks.

These benchmarks define representative queries against the repository
with expected results. They serve as the baseline regression suite
for measuring retrieval quality across sprints.

Each benchmark covers one or more architectural subsystems.
"""

from eval.models import RetrievalTestCase

BENCHMARKS: list[RetrievalTestCase] = [
    # ── Project Initialization ───────────────────────────────────────────
    RetrievalTestCase(
        query="What does ProjectInitializationService do?",
        expected_file_paths=[
            "backend/app/projects/initialization_service.py",
        ],
        expected_concepts=[
            "project initialization",
            "orchestration",
        ],
        expected_symbols=[
            "ProjectInitializationService",
            "open_project",
        ],
    ),
    RetrievalTestCase(
        query="How is a project opened through the API?",
        expected_file_paths=[
            "backend/app/api/routes/projects.py",
            "backend/app/projects/initialization_service.py",
        ],
        expected_concepts=[
            "API endpoint",
            "project lifecycle",
        ],
        expected_symbols=[
            "open_project",
            "POST",
        ],
    ),
    RetrievalTestCase(
        query="What happens when a project is opened?",
        expected_file_paths=[
            "backend/app/projects/initialization_service.py",
            "backend/app/projects/service.py",
            "backend/app/repository/service.py",
            "backend/app/indexing/service.py",
        ],
        expected_concepts=[
            "indexing",
            "scanning",
            "build_index",
            "index_repository",
        ],
        expected_symbols=[
            "open_project",
            "build_index",
            "index_repository",
        ],
    ),
    # ── Repository Scanning ──────────────────────────────────────────────
    RetrievalTestCase(
        query="Which subsystem owns repository scanning?",
        expected_file_paths=[
            "backend/app/repository/scanner.py",
            "backend/app/repository/service.py",
        ],
        expected_concepts=[
            "repository ownership",
            "scanning",
            "filesystem traversal",
        ],
    ),
    RetrievalTestCase(
        query="How does the repository scanner work?",
        expected_file_paths=[
            "backend/app/repository/scanner.py",
            "backend/app/repository/ignore.py",
        ],
        expected_concepts=[
            "walk",
            "ignore patterns",
            ".gitignore",
        ],
        expected_symbols=[
            "scan_directory",
            "is_ignored",
        ],
    ),
    # ── Repository Indexing ──────────────────────────────────────────────
    RetrievalTestCase(
        query="Where are embeddings stored?",
        expected_file_paths=[
            "backend/app/indexing/chroma_store.py",
            "backend/app/indexing/stores.py",
        ],
        expected_concepts=[
            "vector database",
            "ChromaDB",
            "persistent storage",
        ],
        expected_symbols=[
            "ChromaVectorStore",
            "VectorStore",
            "collection",
        ],
    ),
    RetrievalTestCase(
        query="How are code files chunked for indexing?",
        expected_file_paths=[
            "backend/app/repository/chunking.py",
            "backend/app/repository/chunking_algorithms.py",
            "backend/app/repository/python_ast_algorithm.py",
        ],
        expected_concepts=[
            "chunking strategy",
            "AST-based chunking",
            "line-based chunking",
        ],
        expected_symbols=[
            "ChunkingAlgorithm",
            "PythonASTChunking",
        ],
    ),
    # ── Retrieval ────────────────────────────────────────────────────────
    RetrievalTestCase(
        query="How is RetrievalService used?",
        expected_file_paths=[
            "backend/app/indexing/retrieval_service.py",
            "backend/app/indexing/retrieval_models.py",
        ],
        expected_concepts=[
            "semantic search",
            "query embedding",
            "vector search",
        ],
        expected_symbols=[
            "RetrievalService",
            "search",
            "SearchQuery",
            "SearchResult",
        ],
    ),
    RetrievalTestCase(
        query="What is the retrieval score and how is it calculated?",
        expected_file_paths=[
            "backend/app/indexing/retrieval_service.py",
            "backend/app/indexing/retrieval_models.py",
        ],
        expected_concepts=[
            "normalized distance",
            "ranking score",
            "L2 distance",
        ],
        expected_symbols=[
            "_normalize_score",
            "similarity_score",
        ],
    ),
    # ── Context Assembly ────────────────────────────────────────────────
    RetrievalTestCase(
        query="How is repository context assembled into a prompt?",
        expected_file_paths=[
            "backend/app/context_assembly/service.py",
            "backend/app/context_assembly/models.py",
        ],
        expected_concepts=[
            "prompt construction",
            "context formatting",
            "system instruction",
        ],
        expected_symbols=[
            "DefaultContextAssembly",
            "assemble",
            "ContextAssemblyRequest",
        ],
    ),
    RetrievalTestCase(
        query="What files are referenced in the context assembly?",
        expected_file_paths=[
            "backend/app/context_assembly/service.py",
            "backend/app/context_assembly/providers.py",
        ],
        expected_concepts=[
            "abstraction",
            "dependency injection",
        ],
        expected_symbols=[
            "ContextAssembly",
            "DefaultContextAssembly",
        ],
    ),
    # ── Chat ─────────────────────────────────────────────────────────────
    RetrievalTestCase(
        query="How does chat work in RIP?",
        expected_file_paths=[
            "backend/app/chat/service.py",
            "backend/app/chat/models.py",
        ],
        expected_concepts=[
            "chat orchestration",
            "retrieval-augmented generation",
            "streaming",
        ],
        expected_symbols=[
            "ChatService",
            "chat",
            "stream",
        ],
    ),
    RetrievalTestCase(
        query="How is the chat prompt structured?",
        expected_file_paths=[
            "backend/app/chat/models.py",
            "backend/app/context_assembly/service.py",
        ],
        expected_concepts=[
            "ChatMessage",
            "ChatPrompt",
            "system role",
            "user role",
        ],
        expected_symbols=[
            "ChatPrompt",
            "ChatMessage",
            "ChatRole",
        ],
    ),
    # ── Editing ──────────────────────────────────────────────────────────
    RetrievalTestCase(
        query="How does code editing work?",
        expected_file_paths=[
            "backend/app/editing/service.py",
            "backend/app/editing/change_applier.py",
            "backend/app/editing/default_provider.py",
        ],
        expected_concepts=[
            "edit application",
            "change operations",
            "snapshot",
        ],
        expected_symbols=[
            "EditingService",
            "ChangeApplier",
            "DefaultEditingProvider",
        ],
    ),
    RetrievalTestCase(
        query="Where are code snapshots stored?",
        expected_file_paths=[
            "backend/app/editing/snapshot_store.py",
            "backend/app/editing/snapshot_models.py",
        ],
        expected_concepts=[
            "snapshot storage",
            "versioning",
            "rollback",
        ],
        expected_symbols=[
            "SnapshotStore",
            "Snapshot",
        ],
    ),
    # ── Storage ──────────────────────────────────────────────────────────
    RetrievalTestCase(
        query="Where is RIP data stored on disk?",
        expected_file_paths=[
            "backend/app/core/storage/filesystem.py",
            "backend/app/core/storage/models.py",
            "backend/app/core/config/models.py",
        ],
        expected_concepts=[
            "storage abstraction",
            "filesystem persistence",
            "configuration",
        ],
        expected_symbols=[
            "StorageSettings",
            "root_directory",
            "FilesystemStorage",
        ],
    ),
    # ── Dependency Injection ─────────────────────────────────────────────
    RetrievalTestCase(
        query="How are dependencies wired in the application?",
        expected_file_paths=[
            "backend/app/dependencies/providers.py",
        ],
        expected_concepts=[
            "dependency injection",
            "FastAPI dependencies",
            "provider functions",
        ],
        expected_symbols=[
            "get_embedding_provider",
            "get_vector_store_resolver",
            "get_retrieval_service",
            "get_context_assembly",
        ],
    ),
    # ── Architecture Ownership ───────────────────────────────────────────
    RetrievalTestCase(
        query="Which subsystem owns document scanning?",
        expected_file_paths=[
            "backend/app/repository/service.py",
            "backend/app/repository/scanner.py",
        ],
        expected_concepts=[
            "subsystem boundaries",
            "repository ownership",
            "scanning",
        ],
    ),
    RetrievalTestCase(
        query="Which subsystem owns semantic indexing?",
        expected_file_paths=[
            "backend/app/indexing/service.py",
            "backend/app/indexing/indexer.py",
        ],
        expected_concepts=[
            "subsystem boundaries",
            "indexing ownership",
        ],
    ),
    RetrievalTestCase(
        query="What is the data flow from query to answer?",
        expected_file_paths=[
            "backend/app/chat/service.py",
            "backend/app/indexing/retrieval_service.py",
            "backend/app/context_assembly/service.py",
        ],
        expected_concepts=[
            "retrieval-augmented generation",
            "pipeline",
            "search",
            "assemble",
            "generate",
        ],
        expected_symbols=[
            "ChatService",
            "RetrievalService",
            "DefaultContextAssembly",
        ],
    ),
]

__all__ = [
    "BENCHMARKS",
]
