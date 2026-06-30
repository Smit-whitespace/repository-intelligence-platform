"""Project domain models."""

from datetime import UTC
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field


class Project(BaseModel):
    """Opened project metadata."""

    name: str

    root_directory: Path

    storage_directory: Path

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            UTC,
        ),
    )

    @property
    def metadata_file(self) -> Path:
        """Return the project metadata file path."""

        return self.storage_directory / "project.json"