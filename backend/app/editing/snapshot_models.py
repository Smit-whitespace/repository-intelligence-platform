"""Repository Editing snapshot domain models."""

from datetime import UTC
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field


class SnapshotFile(BaseModel):
    """Snapshot of a single repository file."""

    relative_path: Path

    existed: bool

    content: str

    applied_sha256: str | None = None
    """SHA-256 of the content written by the apply.

    Rollback compares it with the file's current content so it never
    overwrites changes made after the apply. ``None`` for snapshots
    written before this field existed; those skip the check.
    """


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