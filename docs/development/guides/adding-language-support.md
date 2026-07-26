# Guide: Adding Language Support

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Objective

Add AST-aware chunking for a new programming language while preserving the chunking registry pattern.

## Steps

### 1. Implement the Algorithm

```python
from app.repository.chunking_algorithms import ChunkAlgorithm
from app.repository.models import ChunkBoundary, RepositoryDocument


class RustChunkAlgorithm(ChunkAlgorithm):
    """AST-aware chunking for Rust."""

    def generate_boundaries(
        self,
        document: RepositoryDocument,
    ) -> list[ChunkBoundary]:
        """Generate chunk boundaries from Rust AST."""
        # Parse the document, find function/item boundaries
        # Return list of ChunkBoundary(start_line, end_line)
```

### 2. Register the Algorithm

In `app/repository/chunking.py` or at application startup:

```python
chunker = RepositoryChunker()
chunker.register_algorithm("Rust", RustChunkAlgorithm())
```

Or add to the default `_language_algorithms` dict in `RepositoryChunker.__init__()`.

### 3. Ensure Language Detection

Verify that `RepositoryMetadataExtractor` detects the new language. Update language detection in `app/repository/languages.py` or `app/repository/filetypes.py` if the language isn't recognized by file extension.

### 4. Verify

- Repository scan detects files with the new language
- Chunks are produced with correct language metadata
- All existing tests pass

## Design Notes

- The chunking registry pattern was chosen specifically to make adding languages additive
- No changes to `IndexingService`, `RetrievalService`, or any downstream subsystem
- Line-based chunking is the fallback for any language without a registered algorithm

## Related

- [Repository Architecture](../../architecture/backend/repository.md)
- ADR-0015: Chunking Strategy
