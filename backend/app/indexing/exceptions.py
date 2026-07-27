"""Indexing exceptions."""


class IndexingError(Exception):
    """Base indexing exception."""


class EmbeddingError(IndexingError):
    """Embedding generation failed."""


class VectorStoreError(IndexingError):
    """Vector store operation failed."""
