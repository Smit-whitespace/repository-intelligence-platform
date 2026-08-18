"""Project-scoped vector store resolution.

Every project owns its own persistent vector store at a location derived
exclusively from the project root directory:

    <root>/.local_openclaw/index/chroma

Because the location derives from the project root — never the process
working directory — the same project resolves to the same index no
matter where RIP is launched from, and different projects can never
read each other's chunks.
"""

from pathlib import Path
from typing import Protocol

from app.core.storage.locations import project_chroma_directory
from chromadb.api.shared_system_client import (
    SharedSystemClient,
)

from app.indexing.chroma_store import ChromaVectorStore
from app.indexing.stores import VectorStore


class VectorStoreResolver(Protocol):
    """Resolve the vector store for a project root directory."""

    def for_project(
        self,
        root_directory: str,
        *,
        create: bool = False,
    ) -> VectorStore | None:
        """Return the store for a project, or None when unavailable.

        When ``create`` is False and the project has never been indexed,
        the resolver returns None instead of creating an empty store.
        """


class ProjectChromaStoreResolver:
    """Resolve the persistent Chroma store for a project root.

    Stores are cached per project for the process lifetime so repeated
    retrieval does not reopen the Chroma database.
    """

    def __init__(
        self,
        collection_name: str,
    ) -> None:
        """Initialize the resolver."""

        self._collection_name = collection_name

        self._stores: dict[Path, VectorStore] = {}

    def for_project(
        self,
        root_directory: str,
        *,
        create: bool = False,
    ) -> VectorStore | None:
        """Return the store for the given project root directory."""

        if not root_directory:
            return None

        persist_directory = project_chroma_directory(
            root_directory,
        )

        if not create and not persist_directory.exists():
            return None

        store = self._stores.get(
            persist_directory,
        )

        if store is None:
            store = ChromaVectorStore(
                persist_directory=persist_directory,
                collection_name=self._collection_name,
            )

            self._stores[
                persist_directory
            ] = store

        return store

    def close_all(self) -> None:
        """Close every cached store and release its file handles.

        The shared Chroma system cache is cleared only after every
        store has been stopped, so later lookups can create fresh
        systems for reopened projects.
        """

        stores = list(
            self._stores.values(),
        )

        self._stores.clear()

        for store in stores:
            close = getattr(
                store,
                "close",
                None,
            )

            if callable(close):
                close()

        SharedSystemClient.clear_system_cache()


class StaticVectorStoreResolver:
    """Resolve a single fixed store for any project root.

    Used by tests and evaluation harnesses that operate on one store
    directly instead of the project-scoped persistence layout.
    """

    def __init__(
        self,
        vector_store: VectorStore,
    ) -> None:
        """Initialize the resolver."""

        self._vector_store = vector_store

    def for_project(
        self,
        root_directory: str,
        *,
        create: bool = False,
    ) -> VectorStore | None:
        """Return the fixed store for any project root."""

        del root_directory, create

        return self._vector_store
