"""Transport models for Repository Editing endpoints."""

from pathlib import Path

from pydantic import BaseModel

from app.editing.models import (
    ChangeSet,
)


class ApplyRequest(BaseModel):
    """Request to apply a previously planned ChangeSet."""

    repository_root: Path

    change_set: ChangeSet