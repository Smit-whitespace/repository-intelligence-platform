"""Project API schemas."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class OpenProjectRequest(BaseModel):
    """Open project request."""

    root_directory: Path


class OpenProjectResponse(BaseModel):
    """Open project response."""

    project: str
    root_directory: Path


class ProjectInfoResponse(BaseModel):
    """Project information response."""

    name: str
    root_directory: Path
    storage_directory: Path
    created_at: datetime