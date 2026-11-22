"""Safety guarantees of the editing engine.

These tests use the real ChangeApplier and the real project-scoped
snapshot store, so they exercise the actual filesystem behavior:
registered-root binding, protected paths, stale-edit and rollback
conflict detection, exact line-ending preservation, and all-or-nothing
multi-file apply.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.storage.locations import (
    project_metadata_path,
    project_snapshots_directory,
)
from app.dependencies.providers import (
    get_editing_service,
    get_snapshot_store_factory,
)
from app.editing.change_applier import ChangeApplier
from app.editing.default_provider import DefaultEditingProvider
from app.editing.exceptions import (
    EditConflictError,
    EditingError,
    IncompleteRevertError,
    UnregisteredRepositoryError,
)
from app.editing.models import (
    ChangeSet,
    FileEdit,
)
from app.editing.service import EditingService
from app.main import app


def _register_project(
    root: Path,
) -> Path:
    """Mark a directory as a registered RIP project."""

    metadata_path = project_metadata_path(
        root,
    )

    metadata_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata_path.write_bytes(
        "{}".encode(),
    )

    return root


def _service(
    change_applier: ChangeApplier | None = None,
) -> EditingService:
    """Build an editing service with real collaborators."""

    return EditingService(
        editing_provider=DefaultEditingProvider(),
        change_applier=change_applier or ChangeApplier(),
        snapshot_store_factory=get_snapshot_store_factory(),
    )


def _edit(
    path: str,
    original: str,
    updated: str,
) -> FileEdit:
    return FileEdit(
        relative_path=Path(
            path,
        ),
        original_content=original,
        updated_content=updated,
    )


def _snapshot_files(
    root: Path,
) -> list[Path]:
    directory = project_snapshots_directory(
        root,
    )

    if not directory.exists():
        return []

    return sorted(
        directory.iterdir(),
    )


# --- Registered-root binding ---------------------------------------------


def test_apply_rejects_unregistered_root(
    tmp_path: Path,
) -> None:
    """An arbitrary directory cannot be used as an editing root."""

    with pytest.raises(
        UnregisteredRepositoryError,
    ):
        _service().apply(
            repository_root=tmp_path,
            change_set=ChangeSet(
                edits=[
                    _edit("evil.txt", "", "x"),
                ],
            ),
        )

    assert not (tmp_path / "evil.txt").exists()

    # No project storage may be created as a side effect.
    assert not (tmp_path / ".local_openclaw").exists()


def test_rollback_and_plan_reject_unregistered_root(
    tmp_path: Path,
) -> None:
    """Rollback and planning are bound to registered roots too."""

    service = _service()

    with pytest.raises(
        UnregisteredRepositoryError,
    ):
        service.rollback(
            repository_root=tmp_path,
            snapshot_id="anything",
        )

    from app.editing.models import EditRequest

    with pytest.raises(
        UnregisteredRepositoryError,
    ):
        service.edit(
            EditRequest(
                repository_root=tmp_path,
                instruction="create file notes.md",
            ),
        )


# --- Protected paths -----------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        ".git/hooks/pre-commit",
        ".GIT/config",
        "sub/.git/config",
        ".local_openclaw/snapshots/forged.json",
        ".Local_OpenClaw/project.json",
    ],
)
def test_apply_rejects_protected_paths(
    tmp_path: Path,
    path: str,
) -> None:
    """Edits can never write into .git or RIP's own storage."""

    root = _register_project(
        tmp_path,
    )

    with pytest.raises(
        EditingError,
        match="protected path",
    ):
        _service().apply(
            repository_root=root,
            change_set=ChangeSet(
                edits=[
                    _edit(path, "", "payload"),
                ],
            ),
        )

    assert not (root / ".git").exists()


def test_apply_rejects_symlink_into_protected_directory(
    tmp_path: Path,
) -> None:
    """A symlink cannot be used to smuggle a write into .git."""

    root = _register_project(
        tmp_path,
    )

    (root / ".git").mkdir()

    try:
        os.symlink(
            root / ".git",
            root / "innocent",
            target_is_directory=True,
        )

    except (OSError, NotImplementedError):
        pytest.skip(
            "Creating symlinks is not permitted on this system.",
        )

    with pytest.raises(
        EditingError,
        match="protected path",
    ):
        ChangeApplier().apply(
            repository_root=root,
            change_set=ChangeSet(
                edits=[
                    _edit("innocent/config", "", "payload"),
                ],
            ),
        )


# --- Stale edits and rollback conflicts ----------------------------------


def test_apply_rejects_edit_planned_against_old_content(
    tmp_path: Path,
) -> None:
    """A file changed after planning is never silently overwritten."""

    root = _register_project(
        tmp_path,
    )

    target = root / "main.py"

    target.write_bytes(
        "changed by the user\n".encode(),
    )

    with pytest.raises(
        EditConflictError,
        match="main.py",
    ):
        _service().apply(
            repository_root=root,
            change_set=ChangeSet(
                edits=[
                    _edit("main.py", "planned against this\n", "new\n"),
                ],
            ),
        )

    assert target.read_bytes() == "changed by the user\n".encode()

    # Nothing was applied, so no snapshot should be left behind.
    assert _snapshot_files(root) == []


def test_apply_rejects_creating_a_file_that_appeared_after_planning(
    tmp_path: Path,
) -> None:
    """An edit planned as "create" conflicts with a file that now exists."""

    root = _register_project(
        tmp_path,
    )

    (root / "notes.md").write_bytes(
        "someone else's notes".encode(),
    )

    with pytest.raises(
        EditConflictError,
    ):
        ChangeApplier().apply(
            repository_root=root,
            change_set=ChangeSet(
                edits=[
                    _edit("notes.md", "", "mine"),
                ],
            ),
        )


def test_rollback_round_trip_restores_original_state(
    tmp_path: Path,
) -> None:
    """Rollback restores modified files and removes created ones."""

    root = _register_project(
        tmp_path,
    )

    (root / "main.py").write_bytes(
        "old\n".encode(),
    )

    service = _service()

    snapshot_id = service.apply(
        repository_root=root,
        change_set=ChangeSet(
            edits=[
                _edit("main.py", "old\n", "new\n"),
                _edit("pkg/created.py", "", "created\n"),
            ],
        ),
    )

    service.rollback(
        repository_root=root,
        snapshot_id=snapshot_id,
    )

    assert (root / "main.py").read_bytes() == "old\n".encode()

    assert not (root / "pkg/created.py").exists()


def test_rollback_refuses_to_overwrite_changes_made_after_apply(
    tmp_path: Path,
) -> None:
    """Rollback detects edits made after the apply and stops."""

    root = _register_project(
        tmp_path,
    )

    target = root / "main.py"

    target.write_bytes(
        "old\n".encode(),
    )

    service = _service()

    snapshot_id = service.apply(
        repository_root=root,
        change_set=ChangeSet(
            edits=[
                _edit("main.py", "old\n", "new\n"),
            ],
        ),
    )

    target.write_bytes(
        "new\nplus later work\n".encode(),
    )

    with pytest.raises(
        EditConflictError,
        match="main.py",
    ):
        service.rollback(
            repository_root=root,
            snapshot_id=snapshot_id,
        )

    assert target.read_bytes() == "new\nplus later work\n".encode()


def test_rollback_refuses_when_applied_file_was_deleted(
    tmp_path: Path,
) -> None:
    """A file deleted after apply also counts as a later change."""

    root = _register_project(
        tmp_path,
    )

    service = _service()

    snapshot_id = service.apply(
        repository_root=root,
        change_set=ChangeSet(
            edits=[
                _edit("created.py", "", "x\n"),
            ],
        ),
    )

    (root / "created.py").unlink()

    with pytest.raises(
        EditConflictError,
    ):
        service.rollback(
            repository_root=root,
            snapshot_id=snapshot_id,
        )


# --- Line endings --------------------------------------------------------


def test_apply_writes_content_byte_for_byte(
    tmp_path: Path,
) -> None:
    """LF stays LF and CRLF stays CRLF, on every platform."""

    root = _register_project(
        tmp_path,
    )

    (root / "crlf.txt").write_bytes(
        b"one\r\ntwo\r\n",
    )

    ChangeApplier().apply(
        repository_root=root,
        change_set=ChangeSet(
            edits=[
                _edit("crlf.txt", "one\r\ntwo\r\n", "one\r\ntwo\r\nthree\r\n"),
                _edit("lf.txt", "", "a\nb\n"),
            ],
        ),
    )

    assert (root / "crlf.txt").read_bytes() == b"one\r\ntwo\r\nthree\r\n"

    assert (root / "lf.txt").read_bytes() == b"a\nb\n"


def test_crlf_edit_planned_with_lf_content_is_a_conflict(
    tmp_path: Path,
) -> None:
    """Original content is compared exactly, including line endings."""

    root = _register_project(
        tmp_path,
    )

    (root / "crlf.txt").write_bytes(
        b"one\r\n",
    )

    with pytest.raises(
        EditConflictError,
    ):
        ChangeApplier().apply(
            repository_root=root,
            change_set=ChangeSet(
                edits=[
                    _edit("crlf.txt", "one\n", "two\n"),
                ],
            ),
        )


def test_rollback_restores_crlf_bytes_exactly(
    tmp_path: Path,
) -> None:
    """Snapshots keep CRLF, so rollback restores the exact bytes."""

    root = _register_project(
        tmp_path,
    )

    target = root / "win.txt"

    target.write_bytes(
        b"line 1\r\nline 2\r\n",
    )

    service = _service()

    snapshot_id = service.apply(
        repository_root=root,
        change_set=ChangeSet(
            edits=[
                _edit("win.txt", "line 1\r\nline 2\r\n", "replaced\n"),
            ],
        ),
    )

    service.rollback(
        repository_root=root,
        snapshot_id=snapshot_id,
    )

    assert target.read_bytes() == b"line 1\r\nline 2\r\n"


def test_planner_reports_original_content_with_exact_line_endings(
    tmp_path: Path,
) -> None:
    """A plan made from a CRLF file can be applied without a conflict."""

    root = _register_project(
        tmp_path,
    )

    (root / "notes.md").write_bytes(
        b"# Notes\r\n",
    )

    from app.editing.models import EditRequest

    response = _service().edit(
        EditRequest(
            repository_root=root,
            instruction="create file notes.md",
        ),
    )

    assert response.change_set.edits[0].original_content == "# Notes\r\n"


# --- All-or-nothing apply ------------------------------------------------


class _FailOnNthWrite(ChangeApplier):
    """ChangeApplier whose Nth atomic write fails."""

    def __init__(
        self,
        fail_on: int,
        fail_reverts: bool = False,
    ) -> None:
        self._fail_on = fail_on
        self._fail_reverts = fail_reverts
        self._writes = 0

    def _write_file_atomic(
        self,
        target_path: Path,
        content: str,
    ) -> None:
        self._writes += 1

        if self._writes == self._fail_on or (
            self._fail_reverts and self._writes > self._fail_on
        ):
            raise OSError(
                "disk full",
            )

        super()._write_file_atomic(
            target_path=target_path,
            content=content,
        )


def test_failed_multi_file_apply_reverts_every_written_file(
    tmp_path: Path,
) -> None:
    """If the third write fails, the first two are undone."""

    root = _register_project(
        tmp_path,
    )

    (root / "a.py").write_bytes(
        "a\n".encode(),
    )

    with pytest.raises(
        EditingError,
        match="reverted",
    ):
        _service(
            _FailOnNthWrite(
                fail_on=3,
            ),
        ).apply(
            repository_root=root,
            change_set=ChangeSet(
                edits=[
                    _edit("a.py", "a\n", "A\n"),
                    _edit("b.py", "", "B\n"),
                    _edit("c.py", "", "C\n"),
                ],
            ),
        )

    assert (root / "a.py").read_bytes() == "a\n".encode()

    assert not (root / "b.py").exists()

    assert not (root / "c.py").exists()

    assert _snapshot_files(root) == []


def test_incomplete_revert_keeps_snapshot_and_names_it(
    tmp_path: Path,
) -> None:
    """When the revert also fails, the snapshot is the way back."""

    root = _register_project(
        tmp_path,
    )

    (root / "a.py").write_bytes(
        "a\n".encode(),
    )

    with pytest.raises(
        IncompleteRevertError,
    ) as error:
        _service(
            _FailOnNthWrite(
                fail_on=2,
                fail_reverts=True,
            ),
        ).apply(
            repository_root=root,
            change_set=ChangeSet(
                edits=[
                    _edit("a.py", "a\n", "A\n"),
                    _edit("b.py", "", "B\n"),
                ],
            ),
        )

    snapshots = _snapshot_files(
        root,
    )

    assert len(snapshots) == 1

    assert snapshots[0].stem in str(error.value)


# --- HTTP status mapping -------------------------------------------------


def test_api_maps_safety_errors_to_status_codes(
    tmp_path: Path,
) -> None:
    """Unregistered roots are 403 and conflicts are 409."""

    app.dependency_overrides[
        get_editing_service
    ] = lambda: _service()

    client = TestClient(
        app,
    )

    try:
        unregistered = client.post(
            "/api/v1/editing/apply",
            json={
                "repository_root": str(tmp_path),
                "change_set": {
                    "edits": [],
                },
            },
        )

        root = _register_project(
            tmp_path,
        )

        (root / "main.py").write_bytes(
            "current".encode(),
        )

        conflict = client.post(
            "/api/v1/editing/apply",
            json={
                "repository_root": str(root),
                "change_set": {
                    "edits": [
                        {
                            "relative_path": "main.py",
                            "original_content": "stale",
                            "updated_content": "new",
                        },
                    ],
                },
            },
        )

    finally:
        app.dependency_overrides.clear()

    assert unregistered.status_code == 403

    assert conflict.status_code == 409
