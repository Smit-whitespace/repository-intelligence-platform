"""Tests for the Editing service."""

from pathlib import Path

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
from app.core.storage.abstractions import (
    StorageProvider,
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

        self.snapshot = None

    def save(
        self,
        snapshot,
    ) -> None:
        self.snapshot = snapshot

    def load(
        self,
        snapshot_id: str,
    ):
        raise AssertionError(
            "Unexpected call.",
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
    """Editing service should create a snapshot before execution."""

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

    service.apply(
        repository_root=repository_root,
        change_set=change_set,
    )

    assert (
        snapshot_store.snapshot
        is not None
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
    ) -> dict:
        raise AssertionError(
            "Unexpected call.",
        )

    def write_json(
        self,
        path: Path,
        data: dict,
    ) -> None:
        pass

    def delete(
        self,
        path: Path,
    ) -> None:
        raise AssertionError(
            "Unexpected call.",
        )