"""Project API schemas."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.indexing.models import IndexingDiagnostics


class OpenProjectRequest(BaseModel):
    """Open project request."""

    root_directory: Path = Field(
        description="Absolute path to the project root directory.",
        examples=[
            "/home/user/projects/my-project",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "root_directory": "/home/user/projects/my-project",
            },
        },
    )


class OpenProjectResponse(BaseModel):
    """Open project response."""

    project: str = Field(
        description="Project display name derived from the root directory.",
        examples=[
            "my-project",
        ],
    )

    root_directory: Path = Field(
        description="Absolute path to the opened project root directory.",
        examples=[
            "/home/user/projects/my-project",
        ],
    )

    indexing_diagnostics: IndexingDiagnostics | None = Field(
        default=None,
        description="Indexing diagnostics from the initial repository scan.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project": "my-project",
                "root_directory": "/home/user/projects/my-project",
            },
        },
    )


class ProjectInfoResponse(BaseModel):
    """Project information response."""

    name: str = Field(
        description="Project display name.",
        examples=[
            "my-project",
        ],
    )

    root_directory: Path = Field(
        description="Absolute path to the project root directory.",
        examples=[
            "/home/user/projects/my-project",
        ],
    )

    storage_directory: Path = Field(
        description="Absolute path to the project metadata directory.",
        examples=[
            "/home/user/projects/my-project/.local_openclaw",
        ],
    )

    created_at: datetime = Field(
        description="UTC timestamp when the project metadata was created.",
        examples=[
            "2026-07-15T10:30:00Z",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "my-project",
                "root_directory": "/home/user/projects/my-project",
                "storage_directory": (
                    "/home/user/projects/my-project/.local_openclaw"
                ),
                "created_at": "2026-07-15T10:30:00Z",
            },
        },
    )
