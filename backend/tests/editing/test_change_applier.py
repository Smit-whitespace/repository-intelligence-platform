"""Tests for the ChangeApplier."""

from pathlib import Path

import pytest

from app.editing.change_applier import (
    ChangeApplier,
)
from app.editing.models import (
    ChangeSet,
    FileEdit,
)
from app.editing.snapshot_models import (
    Snapshot,
    SnapshotFile,
)
from app.editing.exceptions import (
    EditingError,
)

def test_create_new_file(
    tmp_path: Path,
) -> None:
    """New files should be created."""

    applier = ChangeApplier()

    applier.apply(
        repository_root=tmp_path,
        change_set=ChangeSet(
            edits=[
                FileEdit(
                    relative_path=Path(
                        "README.md",
                    ),
                    original_content="",
                    updated_content="Hello",
                ),
            ],
        ),
    )

    assert (
        tmp_path
        / "README.md"
    ).read_text(
        encoding="utf-8",
    ) == "Hello"


def test_replace_existing_file(
    tmp_path: Path,
) -> None:
    """Existing files should be replaced."""

    file_path = (
        tmp_path
        / "README.md"
    )

    file_path.write_text(
        "Old",
        encoding="utf-8",
    )

    applier = ChangeApplier()

    applier.apply(
        repository_root=tmp_path,
        change_set=ChangeSet(
            edits=[
                FileEdit(
                    relative_path=Path(
                        "README.md",
                    ),
                    original_content="Old",
                    updated_content="New",
                ),
            ],
        ),
    )

    assert (
        file_path.read_text(
            encoding="utf-8",
        )
        == "New"
    )


def test_create_parent_directories(
    tmp_path: Path,
) -> None:
    """Parent directories should be created."""

    applier = ChangeApplier()

    applier.apply(
        repository_root=tmp_path,
        change_set=ChangeSet(
            edits=[
                FileEdit(
                    relative_path=Path(
                        "docs/guide.md",
                    ),
                    original_content="",
                    updated_content="Guide",
                ),
            ],
        ),
    )

    assert (
        tmp_path
        / "docs"
        / "guide.md"
    ).exists()


def test_reject_path_escape(
    tmp_path: Path,
) -> None:
    """Repository escape should fail."""

    applier = ChangeApplier()

    with pytest.raises(
        EditingError,
    ):
        applier.apply(
            repository_root=tmp_path,
            change_set=ChangeSet(
                edits=[
                    FileEdit(
                        relative_path=Path(
                            "../outside.txt",
                        ),
                        original_content="",
                        updated_content="Bad",
                    ),
                ],
            ),
        )

def test_duplicate_paths_are_rejected(
    tmp_path: Path,
) -> None:
    """Duplicate edits should fail validation."""

    applier = ChangeApplier()

    with pytest.raises(
        EditingError,
    ):
        applier.apply(
            repository_root=tmp_path,
            change_set=ChangeSet(
                edits=[
                    FileEdit(
                        relative_path=Path("README.md"),
                        original_content="",
                        updated_content="1",
                    ),
                    FileEdit(
                        relative_path=Path("README.md"),
                        original_content="",
                        updated_content="2",
                    ),
                ],
            ),
        )

def test_empty_relative_path_is_rejected(
    tmp_path: Path,
) -> None:
    """Empty paths should fail validation."""

    applier = ChangeApplier()

    with pytest.raises(
        EditingError,
    ):
        applier.apply(
            repository_root=tmp_path,
            change_set=ChangeSet(
                edits=[
                    FileEdit(
                        relative_path=Path(),
                        original_content="",
                        updated_content="",
                    ),
                ],
            ),
        )

def test_invalid_changeset_performs_no_writes(
    tmp_path: Path,
) -> None:
    """Validation should occur before execution."""

    applier = ChangeApplier()

    with pytest.raises(
        EditingError,
    ):
        applier.apply(
            repository_root=tmp_path,
            change_set=ChangeSet(
                edits=[
                    FileEdit(
                        relative_path=Path("README.md"),
                        original_content="",
                        updated_content="Hello",
                    ),
                    FileEdit(
                        relative_path=Path("README.md"),
                        original_content="",
                        updated_content="World",
                    ),
                ],
            ),
        )

    assert not (
        tmp_path / "README.md"
    ).exists()


def test_absolute_relative_path_is_rejected(
    tmp_path: Path,
) -> None:
    """Absolute edit paths should fail validation."""

    target_path = (
        tmp_path
        / "README.md"
    )

    applier = ChangeApplier()

    with pytest.raises(
        EditingError,
    ):
        applier.apply(
            repository_root=tmp_path,
            change_set=ChangeSet(
                edits=[
                    FileEdit(
                        relative_path=target_path,
                        original_content="",
                        updated_content="Bad",
                    ),
                ],
            ),
        )

    assert not target_path.exists()


def test_path_conflict_performs_no_writes(
    tmp_path: Path,
) -> None:
    """File and child-file conflicts should fail before mutation."""

    applier = ChangeApplier()

    with pytest.raises(
        EditingError,
    ):
        applier.apply(
            repository_root=tmp_path,
            change_set=ChangeSet(
                edits=[
                    FileEdit(
                        relative_path=Path(
                            "README.md",
                        ),
                        original_content="",
                        updated_content="Parent file",
                    ),
                    FileEdit(
                        relative_path=Path(
                            "README.md/details.txt",
                        ),
                        original_content="",
                        updated_content="Child file",
                    ),
                ],
            ),
        )

    assert not (
        tmp_path
        / "README.md"
    ).exists()


def test_existing_file_parent_performs_no_writes(
    tmp_path: Path,
) -> None:
    """Existing file parents should fail before earlier edits mutate."""

    (
        tmp_path
        / "README.md"
    ).write_text(
        "Original",
        encoding="utf-8",
    )

    (
        tmp_path
        / "notes.md"
    ).write_text(
        "Original notes",
        encoding="utf-8",
    )

    applier = ChangeApplier()

    with pytest.raises(
        EditingError,
    ):
        applier.apply(
            repository_root=tmp_path,
            change_set=ChangeSet(
                edits=[
                    FileEdit(
                        relative_path=Path(
                            "notes.md",
                        ),
                        original_content="Original notes",
                        updated_content="Changed notes",
                    ),
                    FileEdit(
                        relative_path=Path(
                            "README.md/details.txt",
                        ),
                        original_content="",
                        updated_content="Child file",
                    ),
                ],
            ),
        )

    assert (
        tmp_path
        / "notes.md"
    ).read_text(
        encoding="utf-8",
    ) == "Original notes"


def test_restore_modified_file(
    tmp_path: Path,
) -> None:
    """Existing files should be restored from snapshot content."""

    file_path = (
        tmp_path
        / "README.md"
    )

    file_path.write_text(
        "Changed",
        encoding="utf-8",
    )

    applier = ChangeApplier()

    applier.restore(
        repository_root=tmp_path,
        snapshot=Snapshot(
            snapshot_id="snapshot-1",
            files=[
                SnapshotFile(
                    relative_path=Path(
                        "README.md",
                    ),
                    existed=True,
                    content="Original",
                ),
            ],
        ),
    )

    assert (
        file_path.read_text(
            encoding="utf-8",
        )
        == "Original"
    )


def test_restore_recreates_deleted_file(
    tmp_path: Path,
) -> None:
    """Deleted files should be recreated during restore."""

    applier = ChangeApplier()

    applier.restore(
        repository_root=tmp_path,
        snapshot=Snapshot(
            snapshot_id="snapshot-1",
            files=[
                SnapshotFile(
                    relative_path=Path(
                        "docs/guide.md",
                    ),
                    existed=True,
                    content="Guide",
                ),
            ],
        ),
    )

    assert (
        tmp_path
        / "docs"
        / "guide.md"
    ).read_text(
        encoding="utf-8",
    ) == "Guide"


def test_restore_removes_newly_created_file(
    tmp_path: Path,
) -> None:
    """Files that did not exist at snapshot time should be removed."""

    file_path = (
        tmp_path
        / "new.py"
    )

    file_path.write_text(
        "print('new')",
        encoding="utf-8",
    )

    applier = ChangeApplier()

    applier.restore(
        repository_root=tmp_path,
        snapshot=Snapshot(
            snapshot_id="snapshot-1",
            files=[
                SnapshotFile(
                    relative_path=Path(
                        "new.py",
                    ),
                    existed=False,
                    content="",
                ),
            ],
        ),
    )

    assert not file_path.exists()


def test_restore_rejects_path_escape(
    tmp_path: Path,
) -> None:
    """Snapshot repository escape should fail before restore."""

    target_path = (
        tmp_path
        / "safe.txt"
    )

    target_path.write_text(
        "Safe",
        encoding="utf-8",
    )

    applier = ChangeApplier()

    with pytest.raises(
        EditingError,
    ):
        applier.restore(
            repository_root=tmp_path,
            snapshot=Snapshot(
                snapshot_id="snapshot-1",
                files=[
                    SnapshotFile(
                        relative_path=Path(
                            "safe.txt",
                        ),
                        existed=True,
                        content="Restored",
                    ),
                    SnapshotFile(
                        relative_path=Path(
                            "../outside.txt",
                        ),
                        existed=True,
                        content="Bad",
                    ),
                ],
            ),
        )

    assert (
        target_path.read_text(
            encoding="utf-8",
        )
        == "Safe"
    )
