# ADR-0015: Chunking Strategy

**Status:** Adopted

**Context:**

Repository files must be split into chunks for embedding and retrieval. Different chunking strategies exist: fixed-size, semantic (AST-aware), sliding window. The strategy affects retrieval quality, embedding costs, and storage requirements.

**Decision:**

Chunking uses a registry pattern with language-specific algorithms:

- **Python:** AST-aware chunking via `PythonAstChunkAlgorithm` — splits on function/class boundaries
- **All other languages:** Line-based chunking via `LineChunkAlgorithm` — splits at line boundaries using a configurable target size

New languages can be added by implementing `ChunkAlgorithm` and registering it via `RepositoryChunker.register_algorithm()`.

**Consequences:**

Positive:
- Python chunks are semantically meaningful (function/class aligned)
- Other languages still produce useful chunks
- Adding languages is additive — no existing code changes

Negative:
- Line-based chunks may split mid-function for non-Python languages
- No cross-file or cross-module chunking
- Chunk size is not adaptive per language

**Alternatives Considered:**

- Pure line-based for all languages: rejected — Python AST produces better chunks
- Semantic chunking via ML: rejected — complexity and dependencies exceed current needs
- Fixed token-count chunks: rejected — loses semantic boundaries
