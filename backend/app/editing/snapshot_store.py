"""Repository Editing snapshot persistence."""

from pathlib import Path

from pydantic import ValidationError

from app.core.storage.abstractions import StorageProvider
from app.core.storage.exceptions import (
    StorageError,
    StorageResourceNotFoundError,
)
from app.editing.exceptions import (
    SnapshotNotFoundError,
    SnapshotPersistenceError,
)
from app.editing.snapshot_models import (
    Snapshot,
)

class SnapshotStore:
    """Persist ChangeSet-scoped snapshots."""

    _SNAPSHOT_DIRECTORY = Path(
        "snapshots",
    )

    def __init__(
        self,
        storage: StorageProvider,
    ) -> None:
        """Initialize the snapshot store."""

        self._storage = storage

    def save(
        self,
        snapshot: Snapshot,
    ) -> None:
        """Persist a snapshot."""

        try:
            self._storage.write_json(
                self._snapshot_path(
                    snapshot.snapshot_id,
                ),
                snapshot.model_dump(
                    mode="json",
                ),
            )

        except StorageError as error:
            raise SnapshotPersistenceError(
                "Failed to persist snapshot.",
            ) from error

    def load(
        self,
        snapshot_id: str,
    ) -> Snapshot:
        """Load a previously persisted snapshot."""

        try:
            data = self._storage.read_json(
                self._snapshot_path(
                    snapshot_id,
                ),
            )

        except StorageResourceNotFoundError as error:
            raise SnapshotNotFoundError(
                "Snapshot not found.",
            ) from error

        except StorageError as error:
            raise SnapshotPersistenceError(
                "Failed to load snapshot.",
            ) from error

        try:
            return Snapshot.model_validate(
                data,
            )

        except ValidationError as error:
            raise SnapshotPersistenceError(
                "Failed to load snapshot.",
            ) from error

    def delete(
        self,
        snapshot_id: str,
    ) -> None:
        """Delete a persisted snapshot."""

        try:
            self._storage.delete(
                self._snapshot_path(
                    snapshot_id,
                ),
            )

        except StorageResourceNotFoundError as error:
            raise SnapshotNotFoundError(
                "Snapshot not found.",
            ) from error

        except StorageError as error:
            raise SnapshotPersistenceError(
                "Failed to delete snapshot.",
            ) from error

    def _snapshot_path(
        self,
        snapshot_id: str,
    ) -> Path:
        """Return the storage path for a snapshot."""

        return (
            self._SNAPSHOT_DIRECTORY
            / f"{snapshot_id}.json"
        )
