"""Repository Editing domain models."""

from pathlib import Path

from pydantic import BaseModel


class EditRequest(BaseModel):
    """Request to modify a repository."""

    repository_root: Path

    instruction: str


class FileEdit(BaseModel):
    """A proposed modification to a single file."""

    relative_path: Path

    original_content: str

    updated_content: str


class ChangeSet(BaseModel):
    """A collection of proposed file modifications."""

    edits: list[FileEdit]


class EditResponse(BaseModel):
    """Result of an editing operation."""

    change_set: ChangeSet