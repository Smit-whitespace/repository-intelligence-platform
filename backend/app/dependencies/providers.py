"""Dependency provider implementations."""

from functools import lru_cache

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
from app.core.storage.abstractions import StorageProvider
from app.core.storage.filesystem import FileSystemStorage
from app.editing.default_provider import (
    DefaultEditingProvider,
)
from app.editing.providers import (
    EditingProvider,
)
from app.editing.service import (
    EditingService,
)
from app.indexing.chroma_store import (
    ChromaVectorStore,
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
from app.indexing.stores import (
    VectorStore,
)
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner
from app.repository.service import RepositoryService


@lru_cache(maxsize=1)
def get_storage() -> StorageProvider:
    """Return the application storage provider."""

    storage = FileSystemStorage(
        root_directory=settings.storage.root_directory,
    )

    storage.initialize()

    return storage


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
def get_repository_metadata_extractor(
) -> RepositoryMetadataExtractor:
    """Return the repository metadata extractor."""

    return RepositoryMetadataExtractor()


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
def get_vector_store() -> VectorStore:
    """Return the vector store."""

    return ChromaVectorStore(
        settings.chroma,
    )


@lru_cache(maxsize=1)
def get_retrieval_service() -> RetrievalService:
    """Return the retrieval service."""

    return RetrievalService(
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
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
    )