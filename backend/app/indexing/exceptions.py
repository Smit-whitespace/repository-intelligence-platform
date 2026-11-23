"""Indexing exceptions."""


class IndexingError(Exception):
    """Base indexing exception."""


class EmbeddingError(IndexingError):
    """Embedding generation failed."""


class VectorStoreError(IndexingError):
    """Vector store operation failed."""


class IndexIncompatibleError(IndexingError):
    """The project index was built with a different embedding model.

    Vectors from different embedding models are not comparable (and
    usually differ in dimension), so searching such an index would
    return meaningless results. The fix is an explicit reindex.
    """


class IndexingBusyError(IndexingError):
    """Another process holds the project's index lock (HTTP 409)."""
