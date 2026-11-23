"""Repository Editing snapshot persistence."""

from pathlib import Path

from pydantic import ValidationError

from app.core.storage.abstractions import StorageProvider
from app.core.storage.integrity import sign, verify
from app.core.storage.exceptions import (
    StorageError,
    StorageResourceNotFoundError,
)
from app.editing.exceptions import (
    SnapshotNotFoundError,
    SnapshotPersistenceError,
    UntrustedStateError,
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
        repository_root: Path | None = None,
    ) -> None:
        """Initialize the snapshot store.

        Snapshots are signed and bound to ``repository_root``; see
        ``app/core/storage/integrity.py``.
        """

        self._storage = storage

        self._root = repository_root

    def save(
        self,
        snapshot: Snapshot,
    ) -> None:
        """Persist a snapshot."""

        data = snapshot.model_dump(
            mode="json",
        )

        try:
            self._storage.write_json(
                self._snapshot_path(
                    snapshot.snapshot_id,
                ),
                {
                    **data,
                    "signature": sign(
                        data,
                        "snapshot",
                        self._root,
                    ),
                },
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

        # Rolling back writes a snapshot's contents into the repository,
        # so only snapshots this installation wrote are trusted.
        signature = data.pop(
            "signature",
            None,
        ) if isinstance(data, dict) else None

        if not verify(
            data,
            signature,
            "snapshot",
            self._root,
        ):
            raise UntrustedStateError(
                "This snapshot was not created by this RIP installation (for "
                "example, it came with a cloned repository), so it cannot be "
                "used for rollback.",
            )

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
