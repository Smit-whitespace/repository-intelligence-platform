"""Project API schemas."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class OpenProjectRequest(BaseModel):
    """Open project request."""

    root_directory: Path = Field(
        description="Absolute path to the project root directory.",
        examples=[
            "A:/Personal Projects/Projects/local-openclaw",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "root_directory": "A:/Personal Projects/Projects/local-openclaw",
            },
        },
    )


class OpenProjectResponse(BaseModel):
    """Open project response."""

    project: str = Field(
        description="Project display name derived from the root directory.",
        examples=[
            "local-openclaw",
        ],
    )

    root_directory: Path = Field(
        description="Absolute path to the opened project root directory.",
        examples=[
            "A:/Personal Projects/Projects/local-openclaw",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project": "local-openclaw",
                "root_directory": "A:/Personal Projects/Projects/local-openclaw",
            },
        },
    )


class ProjectInfoResponse(BaseModel):
    """Project information response."""

    name: str = Field(
        description="Project display name.",
        examples=[
            "local-openclaw",
        ],
    )

    root_directory: Path = Field(
        description="Absolute path to the project root directory.",
        examples=[
            "A:/Personal Projects/Projects/local-openclaw",
        ],
    )

    storage_directory: Path = Field(
        description="Absolute path to the project metadata directory.",
        examples=[
            "A:/Personal Projects/Projects/local-openclaw/.local_openclaw",
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
                "name": "local-openclaw",
                "root_directory": "A:/Personal Projects/Projects/local-openclaw",
                "storage_directory": (
                    "A:/Personal Projects/Projects/local-openclaw/.local_openclaw"
                ),
                "created_at": "2026-07-15T10:30:00Z",
            },
        },
    )
