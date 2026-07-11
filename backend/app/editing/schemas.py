"""Editing API schemas."""

from pathlib import Path

from pydantic import BaseModel


class EditRepositoryRequest(BaseModel):
    """Incoming repository editing request."""

    instruction: str


class FileEditResponse(BaseModel):
    """Single proposed file modification."""

    relative_path: Path

    original_content: str

    updated_content: str


class EditRepositoryResponse(BaseModel):
    """Repository editing response."""

    edits: list[FileEditResponse]