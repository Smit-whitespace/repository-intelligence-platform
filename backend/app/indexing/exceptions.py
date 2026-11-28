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


class EmbeddingModelChangedError(IndexingError):
    """The configured embedding model changed while an update was running.

    Raised before anything is written, so vectors from one model are
    never stamped as another's.
    """


class IndexingBusyError(IndexingError):
    """Another indexing run, in this process or another, holds the
    project's index lock (HTTP 409)."""
