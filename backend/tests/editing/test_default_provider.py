"""Tests for the default Editing provider."""

from pathlib import Path

import pytest

from app.editing.default_provider import (
    DefaultEditingProvider,
)
from app.editing.exceptions import (
    InvalidRepositoryError,
)
from app.editing.models import (
    EditRequest,
)


def test_invalid_repository_root_raises(
    tmp_path: Path,
) -> None:
    """Missing repository should raise an exception."""

    provider = DefaultEditingProvider()

    repository_root = (
        tmp_path / "missing"
    )

    with pytest.raises(
        InvalidRepositoryError,
    ):
        provider.edit(
            EditRequest(
                repository_root=repository_root,
                instruction="Create file README.md",
            ),
        )


def test_repository_root_must_be_directory(
    tmp_path: Path,
) -> None:
    """Repository root must be a directory."""

    provider = DefaultEditingProvider()

    repository_root = (
        tmp_path / "file.txt"
    )

    repository_root.write_text(
        "",
    )

    with pytest.raises(
        InvalidRepositoryError,
    ):
        provider.edit(
            EditRequest(
                repository_root=repository_root,
                instruction="Create file README.md",
            ),
        )


def test_create_file_returns_changeset(
    tmp_path: Path,
) -> None:
    """Create file should produce a single FileEdit."""

    provider = DefaultEditingProvider()

    response = provider.edit(
        EditRequest(
            repository_root=tmp_path,
            instruction="Create file README.md",
        ),
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
            "README.md",
        )
    )

    assert (
        edit.original_content
        == ""
    )

    assert (
        edit.updated_content
        == ""
    )


def test_reject_path_outside_repository(
    tmp_path: Path,
) -> None:
    """Path traversal should be rejected."""

    provider = DefaultEditingProvider()

    with pytest.raises(
        InvalidRepositoryError,
    ):
        provider.edit(
            EditRequest(
                repository_root=tmp_path,
                instruction="Create file ../outside.txt",
            ),
        )


def test_repository_relative_path_is_normalized(
    tmp_path: Path,
) -> None:
    """Planned edits should use repository-relative paths."""

    provider = DefaultEditingProvider()

    response = provider.edit(
        EditRequest(
            repository_root=tmp_path,
            instruction="Create file docs/../README.md",
        ),
    )

    assert (
        len(
            response.change_set.edits,
        )
        == 1
    )

    assert (
        response.change_set.edits[
            0
        ].relative_path
        == Path(
            "README.md",
        )
    )

def test_existing_file_preserves_original_content(
    tmp_path: Path,
) -> None:
    """Existing file should populate original_content."""

    provider = DefaultEditingProvider()

    file_path = (
        tmp_path / "README.md"
    )

    file_path.write_text(
        "Existing contents",
        encoding="utf-8",
    )

    response = provider.edit(
        EditRequest(
            repository_root=tmp_path,
            instruction="Create file README.md",
        ),
    )

    edit = response.change_set.edits[0]

    assert (
        edit.original_content
        == "Existing contents"
    )

def test_new_file_has_empty_original_content(
    tmp_path: Path,
) -> None:
    """New file should have no original content."""

    provider = DefaultEditingProvider()

    response = provider.edit(
        EditRequest(
            repository_root=tmp_path,
            instruction="Create file README.md",
        ),
    )

    edit = response.change_set.edits[0]

    assert (
        edit.original_content
        == ""
    )