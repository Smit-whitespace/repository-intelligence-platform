"""Project management service."""

from pathlib import Path

from app.core.storage.exceptions import StorageReadError
from app.core.storage.locations import project_storage_directory
from app.projects.exceptions import (
    InvalidProjectError,
    ProjectNotFoundError,
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

        if _is_too_broad(
            root_directory,
        ):
            raise InvalidProjectError(
                "Refusing to open a home directory or a drive root as a "
                "project. Open the repository folder itself.",
            )

        storage_directory = project_storage_directory(
            root_directory,
        )

        project = Project(
            name=root_directory.name,
            root_directory=root_directory,
            storage_directory=storage_directory,
        )

        # Opening again must not reset when the project was created.
        # Unreadable metadata is simply replaced.
        try:
            project.created_at = self._repository.load(
                storage_directory,
            ).created_at

        except (ProjectNotFoundError, StorageReadError, OSError, ValueError):
            pass

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
            project_storage_directory(
                root_directory,
            ),
        )


def _is_too_broad(
    root_directory: Path,
) -> bool:
    """Return whether a directory is too broad to be a project.

    Registering a project unlocks editing inside it. A home directory or
    filesystem root would put startup folders, shell profiles and SSH
    keys in reach of an edit, so neither can be a project.
    """

    if root_directory.parent == root_directory:
        return True

    try:
        home = Path.home().resolve()

    except RuntimeError:
        return False

    return root_directory == home
