"""Repository Editing domain models."""

from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class EditRequest(BaseModel):
    """Request to modify a repository."""

    repository_root: Path = Field(
        description="Absolute path to the repository root.",
        examples=[
            "A:/Personal Projects/Projects/local-openclaw",
        ],
    )

    instruction: str = Field(
        description="Natural-language editing instruction.",
        examples=[
            "create file docs/notes.md",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "repository_root": "A:/Personal Projects/Projects/local-openclaw",
                "instruction": "create file docs/notes.md",
            },
        },
    )


class FileEdit(BaseModel):
    """A proposed modification to a single file."""

    relative_path: Path = Field(
        description="Repository-relative target file path.",
        examples=[
            "docs/notes.md",
        ],
    )

    original_content: str = Field(
        description="Original file content expected by the edit plan.",
        examples=[
            "",
        ],
    )

    updated_content: str = Field(
        description="Replacement file content to apply.",
        examples=[
            "# Notes\n",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "relative_path": "docs/notes.md",
                "original_content": "",
                "updated_content": "# Notes\n",
            },
        },
    )


class ChangeSet(BaseModel):
    """A collection of proposed file modifications."""

    edits: list[FileEdit] = Field(
        description="Ordered file edits proposed for review and apply.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "edits": [
                    {
                        "relative_path": "docs/notes.md",
                        "original_content": "",
                        "updated_content": "# Notes\n",
                    },
                ],
            },
        },
    )


class EditResponse(BaseModel):
    """Result of an editing operation."""

    change_set: ChangeSet = Field(
        description="Proposed edits for client review.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "change_set": {
                    "edits": [
                        {
                            "relative_path": "docs/notes.md",
                            "original_content": "",
                            "updated_content": "# Notes\n",
                        },
                    ],
                },
            },
        },
    )
