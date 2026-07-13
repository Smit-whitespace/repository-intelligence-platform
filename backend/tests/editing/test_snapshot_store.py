"""Tests for the SnapshotStore."""

from pathlib import Path

import pytest

from app.core.storage.exceptions import (
    StorageReadError,
    StorageWriteError,
)
from app.core.storage.filesystem import (
    FileSystemStorage,
)
from app.editing.exceptions import (
    SnapshotNotFoundError,
    SnapshotPersistenceError,
)
from app.editing.snapshot_models import (
    Snapshot,
    SnapshotFile,
)
from app.editing.snapshot_store import (
    SnapshotStore,
)


def create_storage(
    tmp_path: Path,
) -> FileSystemStorage:
    """Create a filesystem storage provider."""

    storage = FileSystemStorage(
        root_directory=tmp_path,
    )

    storage.initialize()

    return storage


def create_snapshot() -> Snapshot:
    """Create a deterministic snapshot."""

    return Snapshot(
        snapshot_id="snapshot-1",
        files=[
            SnapshotFile(
                relative_path=Path("main.py"),
                content="print('hello')",
            ),
            SnapshotFile(
                relative_path=Path("README.md"),
                content="# README",
            ),
        ],
    )


def test_save_and_load_snapshot(
    tmp_path: Path,
) -> None:
    """Snapshot should survive a save/load round-trip."""

    store = SnapshotStore(
        storage=create_storage(tmp_path),
    )

    snapshot = create_snapshot()

    store.save(
        snapshot,
    )

    loaded = store.load(
        snapshot.snapshot_id,
    )

    assert (
        loaded.snapshot_id
        == snapshot.snapshot_id
    )

    assert (
        loaded.created_at
        == snapshot.created_at
    )

    assert (
        len(
            loaded.files,
        )
        == 2
    )

    assert (
        loaded.files[0].relative_path
        == Path("main.py")
    )

    assert (
        loaded.files[0].content
        == "print('hello')"
    )

    assert (
        loaded.files[1].relative_path
        == Path("README.md")
    )

    assert (
        loaded.files[1].content
        == "# README"
    )


def test_delete_snapshot(
    tmp_path: Path,
) -> None:
    """Deleting a snapshot should remove it."""

    store = SnapshotStore(
        storage=create_storage(tmp_path),
    )

    snapshot = create_snapshot()

    store.save(
        snapshot,
    )

    store.delete(
        snapshot.snapshot_id,
    )

    with pytest.raises(
        SnapshotNotFoundError,
    ):
        store.load(
            snapshot.snapshot_id,
        )


def test_load_missing_snapshot(
    tmp_path: Path,
) -> None:
    """Loading a missing snapshot should fail."""

    store = SnapshotStore(
        storage=create_storage(tmp_path),
    )

    with pytest.raises(
        SnapshotNotFoundError,
    ):
        store.load(
            "does-not-exist",
        )


class WriteFailureStorage(
    FileSystemStorage,
):
    """Storage that fails writes."""

    def write_json(
        self,
        path: Path,
        data: dict,
    ) -> None:
        raise StorageWriteError(
            "boom",
        )


class ReadFailureStorage(
    FileSystemStorage,
):
    """Storage that fails reads."""

    def read_json(
        self,
        path: Path,
    ) -> dict:
        raise StorageReadError(
            "boom",
        )


class DeleteFailureStorage(
    FileSystemStorage,
):
    """Storage that fails deletes."""

    def delete(
        self,
        path: Path,
    ) -> None:
        raise StorageWriteError(
            "boom",
        )


def test_save_translates_storage_error(
    tmp_path: Path,
) -> None:
    """Storage write failures should become Editing exceptions."""

    storage = WriteFailureStorage(
        root_directory=tmp_path,
    )

    storage.initialize()

    store = SnapshotStore(
        storage=storage,
    )

    with pytest.raises(
        SnapshotPersistenceError,
    ):
        store.save(
            create_snapshot(),
        )


def test_load_translates_storage_error(
    tmp_path: Path,
) -> None:
    """Storage read failures should become Editing exceptions."""

    storage = ReadFailureStorage(
        root_directory=tmp_path,
    )

    storage.initialize()

    store = SnapshotStore(
        storage=storage,
    )

    with pytest.raises(
        SnapshotPersistenceError,
    ):
        store.load(
            "snapshot-1",
        )


def test_delete_translates_storage_error(
    tmp_path: Path,
) -> None:
    """Storage delete failures should become Editing exceptions."""

    storage = DeleteFailureStorage(
        root_directory=tmp_path,
    )

    storage.initialize()

    store = SnapshotStore(
        storage=storage,
    )

    with pytest.raises(
        SnapshotPersistenceError,
    ):
        store.delete(
            "snapshot-1",
        )