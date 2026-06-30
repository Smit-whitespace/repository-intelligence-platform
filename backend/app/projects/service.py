"""Project management service."""

from pathlib import Path

from app.projects.exceptions import (
    InvalidProjectError,
)
from app.projects.models import Project
from app.projects.repository import (
    ProjectRepository,
)


class ProjectService:
    """Project management service."""

    def __init__(
        self,
        repository: ProjectRepository,
    ) -> None:
        """Initialize the project service."""

        self._repository = repository

    def open_project(
        self,
        root_directory: Path,
    ) -> Project:
        """Open a project."""

        root_directory = root_directory.resolve()

        if not root_directory.exists():
            raise InvalidProjectError(
                f"Project directory does not exist: "
                f"{root_directory}"
            )

        if not root_directory.is_dir():
            raise InvalidProjectError(
                f"Project path is not a directory: "
                f"{root_directory}"
            )

        project = Project(
            name=root_directory.name,
            root_directory=root_directory,
            storage_directory=(
                root_directory / ".local_openclaw"
            ),
        )

        self._repository.save(
            project,
        )

        return project

    def get_project(
        self,
        root_directory: Path,
    ) -> Project:
        """Return project metadata."""

        return self._repository.load(
            root_directory / ".local_openclaw",
        )