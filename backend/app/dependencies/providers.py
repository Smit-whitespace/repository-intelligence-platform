"""Dependency provider implementations."""

from functools import lru_cache

from app.core.config.settings import settings
from app.core.storage.abstractions import StorageProvider
from app.core.storage.filesystem import FileSystemStorage
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