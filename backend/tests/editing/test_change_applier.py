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