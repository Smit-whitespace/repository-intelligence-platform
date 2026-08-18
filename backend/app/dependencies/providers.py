"""Dependency provider implementations."""

from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from app.chat.ollama_provider import (
    OllamaChatProvider,
)
from app.chat.providers import (
    ChatProvider,
)
from app.chat.service import ChatService
from app.context_assembly.providers import (
    ContextAssembly,
)
from app.context_assembly.service import (
    DefaultContextAssembly,
)
from app.core.config.settings import settings
from app.core.storage.filesystem import FileSystemStorage
from app.core.storage.locations import project_storage_directory
from app.editing.default_provider import (
    DefaultEditingProvider,
)
from app.editing.providers import (
    EditingProvider,
)
from app.editing.service import (
    EditingService,
)
from app.editing.snapshot_store import (
    SnapshotStore,
)
from app.indexing.indexer import (
    RepositoryIndexer,
)
from app.indexing.ollama_provider import (
    OllamaEmbeddingProvider,
)
from app.indexing.providers import (
    EmbeddingProvider,
)
from app.indexing.retrieval_service import (
    RetrievalService,
)
from app.indexing.service import IndexingService
from app.indexing.store_resolver import (
    ProjectChromaStoreResolver,
)
from app.projects.initialization_service import (
    ProjectInitializationService,
)
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService
from app.repository.chunking import (
    RepositoryChunker,
)
from app.repository.documents import (
    RepositoryDocumentLoader,
)
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner
from app.repository.service import RepositoryService
from app.editing.change_applier import (
    ChangeApplier,
)


@lru_cache(maxsize=1)
def get_project_repository() -> ProjectRepository:
    """Return the project repository."""

    return ProjectRepository()


@lru_cache(maxsize=1)
def get_project_service() -> ProjectService:
    """Return the project service."""

    return ProjectService(
        repository=get_project_repository(),
    )


@lru_cache(maxsize=1)
def get_repository_scanner() -> RepositoryScanner:
    """Return the repository scanner."""

    return RepositoryScanner()


@lru_cache(maxsize=1)
def get_repository_metadata_extractor() -> RepositoryMetadataExtractor:
    """Return the repository metadata extractor."""

    return RepositoryMetadataExtractor()


@lru_cache(maxsize=1)
def get_repository_document_loader() -> RepositoryDocumentLoader:
    """Return the repository document loader."""

    return RepositoryDocumentLoader()


@lru_cache(maxsize=1)
def get_repository_chunker() -> RepositoryChunker:
    """Return the repository chunker."""

    return RepositoryChunker()


@lru_cache(maxsize=1)
def get_repository_service() -> RepositoryService:
    """Return the repository service."""

    return RepositoryService(
        scanner=get_repository_scanner(),
        metadata_extractor=get_repository_metadata_extractor(),
    )


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """Return the embedding provider."""

    return OllamaEmbeddingProvider(
        settings.ollama,
    )


@lru_cache(maxsize=1)
def get_vector_store_resolver() -> ProjectChromaStoreResolver:
    """Return the project-scoped vector store resolver."""

    return ProjectChromaStoreResolver(
        collection_name=settings.chroma.collection_name,
    )


@lru_cache(maxsize=1)
def get_repository_indexer() -> RepositoryIndexer:
    """Return the repository indexer."""

    return RepositoryIndexer(
        embedding_provider=get_embedding_provider(),
        vector_store_resolver=get_vector_store_resolver(),
    )


@lru_cache(maxsize=1)
def get_indexing_service() -> IndexingService:
    """Return the indexing service."""

    return IndexingService(
        scanner=get_repository_scanner(),
        metadata_extractor=get_repository_metadata_extractor(),
        document_loader=get_repository_document_loader(),
        chunker=get_repository_chunker(),
        indexer=get_repository_indexer(),
    )


@lru_cache(maxsize=1)
def get_retrieval_service() -> RetrievalService:
    """Return the retrieval service."""

    return RetrievalService(
        embedding_provider=get_embedding_provider(),
        vector_store_resolver=get_vector_store_resolver(),
    )


@lru_cache(maxsize=1)
def get_context_assembly() -> ContextAssembly:
    """Return the Context Assembly service."""

    return DefaultContextAssembly()


@lru_cache(maxsize=1)
def get_chat_provider() -> ChatProvider:
    """Return the chat provider."""

    return OllamaChatProvider(
        settings.ollama,
    )


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """Return the chat service."""

    return ChatService(
        retrieval_service=get_retrieval_service(),
        context_assembly=get_context_assembly(),
        chat_provider=get_chat_provider(),
    )


@lru_cache(maxsize=1)
def get_editing_provider() -> EditingProvider:
    """Return the editing provider."""

    return DefaultEditingProvider()


@lru_cache(maxsize=1)
def get_editing_service() -> EditingService:
    """Return the editing service."""

    return EditingService(
        editing_provider=get_editing_provider(),
        change_applier=get_change_applier(),
        snapshot_store_factory=get_snapshot_store_factory(),
    )


@lru_cache(maxsize=1)
def get_change_applier() -> ChangeApplier:
    """Return the ChangeSet applier."""

    return ChangeApplier()


@lru_cache(maxsize=1)
def get_snapshot_store_factory() -> Callable[[Path], SnapshotStore]:
    """Return a project-scoped snapshot store factory.

    Each project persists snapshots under its own canonical storage
    directory (``<root>/.local_openclaw/snapshots``), derived from the
    project root — never from the process working directory.
    """

    def create_snapshot_store(
        repository_root: Path,
    ) -> SnapshotStore:
        """Create a snapshot store rooted at a project's storage dir."""

        storage = FileSystemStorage(
            root_directory=project_storage_directory(
                repository_root,
            ),
        )

        storage.initialize()

        return SnapshotStore(
            storage=storage,
        )

    return create_snapshot_store


@lru_cache(maxsize=1)
def get_project_initialization_service() -> ProjectInitializationService:
    """Return the project initialization service."""

    return ProjectInitializationService(
        project_service=get_project_service(),
        repository_service=get_repository_service(),
        indexing_service=get_indexing_service(),
    )
