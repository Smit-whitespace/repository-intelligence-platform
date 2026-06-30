"""Project persistence repository."""

from pathlib import Path

from app.core.storage.filesystem import FileSystemStorage
from app.projects.exceptions import ProjectNotFoundError
from app.projects.models import Project


class ProjectRepository:
    """Project persistence repository."""

    _PROJECT_METADATA_FILE = Path("project.json")

    def save(
        self,
        project: Project,
    ) -> None:
        """Persist project metadata."""

        storage = FileSystemStorage(
            root_directory=project.storage_directory,
        )

        storage.initialize()

        storage.write_json(
            self._PROJECT_METADATA_FILE,
            project.model_dump(
                mode="json",
            ),
        )

    def load(
        self,
        storage_directory: Path,
    ) -> Project:
        """Load project metadata."""

        storage = FileSystemStorage(
            root_directory=storage_directory,
        )

        if not storage.exists(
            self._PROJECT_METADATA_FILE,
        ):
            raise ProjectNotFoundError(
                f"Project metadata not found: "
                f"{storage_directory}"
            )

        data = storage.read_json(
            self._PROJECT_METADATA_FILE,
        )

        return Project.model_validate(
            data,
        )

    def exists(
        self,
        storage_directory: Path,
    ) -> bool:
        """Return whether project metadata exists."""

        storage = FileSystemStorage(
            root_directory=storage_directory,
        )

        return storage.exists(
            self._PROJECT_METADATA_FILE,
        )