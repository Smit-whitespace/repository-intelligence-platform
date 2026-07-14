"""Tests for the Editing service."""

from pathlib import Path
from typing import Any

from app.core.storage.abstractions import (
    StorageProvider,
)
from app.editing.change_applier import (
    ChangeApplier,
)
from app.editing.models import (
    ChangeSet,
    EditRequest,
    EditResponse,
    FileEdit,
)
from app.editing.providers import (
    EditingProvider,
)
from app.editing.service import (
    EditingService,
)
from app.editing.snapshot_store import (
    SnapshotStore,
)
from app.editing.snapshot_models import (
    Snapshot,
    SnapshotFile,
)


class FakeEditingProvider(
    EditingProvider,
):
    """Fake Editing provider."""

    def __init__(
        self,
    ) -> None:
        """Initialize the fake provider."""

        self.called = False

        self.request: EditRequest | None = (
            None
        )

    def edit(
        self,
        request: EditRequest,
    ) -> EditResponse:
        """Return a deterministic editing response."""

        self.called = True

        self.request = request

        return EditResponse(
            change_set=ChangeSet(
                edits=[
                    FileEdit(
                        relative_path=Path(
                            "main.py",
                        ),
                        original_content="old",
                        updated_content="new",
                    ),
                ],
            ),
        )


class FakeChangeApplier(
    ChangeApplier,
):
    """Fake ChangeApplier."""

    def __init__(
        self,
    ) -> None:
        """Initialize the fake change applier."""

        self.repository_root: Path | None = (
            None
        )

        self.change_set: ChangeSet | None = (
            None
        )

        self.snapshot: Snapshot | None = (
            None
        )

    def apply(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> None:
        """Record the execution request."""

        self.repository_root = (
            repository_root
        )

        self.change_set = (
            change_set
        )

    def restore(
        self,
        repository_root: Path,
        snapshot: Snapshot,
    ) -> None:
        """Record the restore request."""

        self.repository_root = (
            repository_root
        )

        self.snapshot = snapshot


class FakeSnapshotStore(
    SnapshotStore,
):
    """Fake snapshot store."""

    def __init__(
        self,
    ) -> None:
        super().__init__(
            storage=FakeStorageProvider(),
        )

        self.snapshot: Snapshot | None = None

        self.loaded_snapshot_id: str | None = (
            None
        )

    def save(
        self,
        snapshot: Snapshot,
    ) -> None:
        self.snapshot = snapshot

    def load(
        self,
        snapshot_id: str,
    ) -> Snapshot:
        self.loaded_snapshot_id = snapshot_id

        return Snapshot(
            snapshot_id=snapshot_id,
            files=[
                SnapshotFile(
                    relative_path=Path(
                        "main.py",
                    ),
                    existed=True,
                    content="old",
                ),
            ],
        )

    def delete(
        self,
        snapshot_id: str,
    ) -> None:
        raise AssertionError(
            "Unexpected call.",
        )


def test_edit() -> None:
    """Editing service should delegate to the provider."""

    provider = FakeEditingProvider()

    applier = FakeChangeApplier()

    snapshot_store = FakeSnapshotStore()

    service = EditingService(
        editing_provider=provider,
        change_applier=applier,
        snapshot_store=snapshot_store,
    )

    response = service.edit(
        EditRequest(
            repository_root=Path("."),
            instruction="Rename function.",
        ),
    )

    assert provider.called

    assert (
        provider.request
        is not None
    )

    assert (
        provider.request.instruction
        == "Rename function."
    )

    assert (
        len(
            response.change_set.edits,
        )
        == 1
    )

    edit = response.change_set.edits[0]

    assert (
        edit.relative_path
        == Path(
            "main.py",
        )
    )

    assert (
        edit.original_content
        == "old"
    )

    assert (
        edit.updated_content
        == "new"
    )

    assert (
        snapshot_store.snapshot
        is None
    )


def test_apply() -> None:
    """Editing service should create and return a snapshot before execution."""

    provider = FakeEditingProvider()

    applier = FakeChangeApplier()

    snapshot_store = FakeSnapshotStore()

    service = EditingService(
        editing_provider=provider,
        change_applier=applier,
        snapshot_store=snapshot_store,
    )

    repository_root = Path("/repository")

    change_set = ChangeSet(
        edits=[],
    )

    snapshot_id = service.apply(
        repository_root=repository_root,
        change_set=change_set,
    )

    assert (
        snapshot_store.snapshot
        is not None
    )

    assert (
        snapshot_id
        == snapshot_store.snapshot.snapshot_id
    )

    assert (
        len(
            snapshot_store.snapshot.files,
        )
        == 0
    )

    assert (
        applier.repository_root
        == repository_root
    )

    assert (
        applier.change_set
        == change_set
    )


def test_rollback_loads_snapshot_and_restores() -> None:
    """Rollback should load a snapshot and delegate restore."""

    provider = FakeEditingProvider()

    applier = FakeChangeApplier()

    snapshot_store = FakeSnapshotStore()

    service = EditingService(
        editing_provider=provider,
        change_applier=applier,
        snapshot_store=snapshot_store,
    )

    repository_root = Path(
        "/repository",
    )

    service.rollback(
        repository_root=repository_root,
        snapshot_id="snapshot-1",
    )

    assert (
        snapshot_store.loaded_snapshot_id
        == "snapshot-1"
    )

    assert (
        applier.repository_root
        == repository_root
    )

    assert (
        applier.snapshot
        is not None
    )

    assert (
        applier.snapshot.snapshot_id
        == "snapshot-1"
    )


class FakeStorageProvider(StorageProvider):
    """Fake storage provider."""

    def initialize(self) -> None:
        pass

    def exists(
        self,
        path: Path,
    ) -> bool:
        return False

    def create_directory(
        self,
        path: Path,
    ) -> None:
        pass

    def read_text(
        self,
        path: Path,
    ) -> str:
        raise AssertionError(
            "Unexpected call.",
        )

    def write_text(
        self,
        path: Path,
        content: str,
    ) -> None:
        raise AssertionError(
            "Unexpected call.",
        )

    def read_json(
        self,
        path: Path,
    ) -> dict[str, Any]:
        raise AssertionError(
            "Unexpected call.",
        )

    def write_json(
        self,
        path: Path,
        data: dict[str, Any],
    ) -> None:
        pass

    def delete(
        self,
        path: Path,
    ) -> None:
        raise AssertionError(
            "Unexpected call.",
        )
