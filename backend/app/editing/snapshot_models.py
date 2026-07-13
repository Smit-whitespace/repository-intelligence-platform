"""Repository Editing snapshot domain models."""

from datetime import UTC
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field


class SnapshotFile(BaseModel):
    """Pre-application state of a single repository file."""

    relative_path: Path

    content: str


class Snapshot(BaseModel):
    """ChangeSet-scoped repository snapshot."""

    snapshot_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        ),
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            UTC,
        ),
    )

    files: list[SnapshotFile]