"""Transport models for Repository Editing endpoints."""

from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.editing.models import (
    ChangeSet,
)


class ApplyRequest(BaseModel):
    """Request to apply a previously planned ChangeSet."""

    repository_root: Path = Field(
        description="Absolute path to the repository root.",
        examples=[
            "/home/user/projects/my-project",
        ],
    )

    change_set: ChangeSet = Field(
        description="Reviewed ChangeSet to apply.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "repository_root": "/home/user/projects/my-project",
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


class ApplyResponse(BaseModel):
    """Response returned after applying a ChangeSet."""

    snapshot_id: str = Field(
        description="Server-generated snapshot identifier for rollback.",
        examples=[
            "8f3c7c8c-2d43-48de-8e2f-0b6c43e22f14",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "snapshot_id": "8f3c7c8c-2d43-48de-8e2f-0b6c43e22f14",
            },
        },
    )


class RollbackRequest(BaseModel):
    """Request to restore a previously captured snapshot."""

    repository_root: Path = Field(
        description="Absolute path to the repository root.",
        examples=[
            "/home/user/projects/my-project",
        ],
    )

    snapshot_id: str = Field(
        description="Snapshot identifier returned by apply.",
        examples=[
            "8f3c7c8c-2d43-48de-8e2f-0b6c43e22f14",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "repository_root": "/home/user/projects/my-project",
                "snapshot_id": "8f3c7c8c-2d43-48de-8e2f-0b6c43e22f14",
            },
        },
    )
