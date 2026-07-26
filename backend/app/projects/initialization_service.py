"""Project initialization service."""

from pathlib import Path

from app.indexing.service import IndexingService
from app.projects.models import Project
from app.projects.service import ProjectService
from app.repository.service import RepositoryService


class ProjectInitializationService:
    """Orchestrates project initialization."""

    def __init__(
        self,
        project_service: ProjectService,
        repository_service: RepositoryService,
        indexing_service: IndexingService,
    ) -> None:
        """Initialize the project initialization service."""

        self._project_service = project_service
        self._repository_service = repository_service
        self._indexing_service = indexing_service

    def open_project(
        self,
        root_directory: Path,
    ) -> Project:
        """Open a project and build its index."""

        project = self._project_service.open_project(
            root_directory,
        )

        self._repository_service.build_index(
            root_directory,
        )

        self._indexing_service.index_repository(
            root_directory,
        )

        return project
