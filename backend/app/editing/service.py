"""Repository Editing service."""

from pathlib import Path

from app.editing.change_applier import (
    ChangeApplier,
)
from app.editing.models import (
    ChangeSet,
    EditRequest,
    EditResponse,
)
from app.editing.providers import (
    EditingProvider,
)
from app.editing.snapshot_models import (
    Snapshot,
    SnapshotFile,
)
from app.editing.snapshot_store import (
    SnapshotStore,
)

class EditingService:
    """Repository Editing orchestration service."""

    def __init__(
        self,
        editing_provider: EditingProvider,
        change_applier: ChangeApplier,
        snapshot_store: SnapshotStore,
    ) -> None:
        """Initialize the editing service."""

        self._editing_provider = (
            editing_provider
        )

        self._change_applier = (
            change_applier
        )

        self._snapshot_store = snapshot_store

    def edit(
        self,
        request: EditRequest,
    ) -> EditResponse:
        """Generate repository modifications."""

        return self._editing_provider.edit(
            request,
        )

    def apply(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> None:
        """Apply a previously generated ChangeSet."""

        snapshot = self._create_snapshot(
            repository_root=repository_root,
            change_set=change_set,
        )

        self._snapshot_store.save(
            snapshot,
        )

        self._change_applier.apply(
            repository_root=repository_root,
            change_set=change_set,
        )

    def _create_snapshot(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> Snapshot:
        """Create a ChangeSet-scoped snapshot."""

        files: list[SnapshotFile] = []

        for edit in change_set.edits:
            target_path = (
                repository_root
                / edit.relative_path
            )

            if target_path.exists():
                content = target_path.read_text(
                    encoding="utf-8",
                )
            else:
                content = ""

            files.append(
                SnapshotFile(
                    relative_path=edit.relative_path,
                    content=content,
                ),
            )

        return Snapshot(
            files=files,
        )