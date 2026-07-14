"""Tests for the Editing API."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.dependencies.providers import (
    get_editing_service,
)
from app.editing.models import (
    ChangeSet,
    EditRequest,
    EditResponse,
    FileEdit,
)
from app.editing.service import (
    EditingService,
)
from app.main import app


class FakeEditingService(
    EditingService,
):
    """Fake Editing service."""

    def __init__(
        self,
    ) -> None:
        """Initialize the fake service."""

        self.request: EditRequest | None = (
            None
        )

        self.repository_root: Path | None = (
            None
        )

        self.change_set: ChangeSet | None = (
            None
        )

        self.snapshot_id: str | None = (
            None
        )

    def edit(
        self,
        request: EditRequest,
    ) -> EditResponse:
        """Return a deterministic editing response."""

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

    def apply(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> str:
        """Record an apply request."""

        self.repository_root = repository_root

        self.change_set = change_set

        return "snapshot-1"

    def rollback(
        self,
        repository_root: Path,
        snapshot_id: str,
    ) -> None:
        """Record a rollback request."""

        self.repository_root = repository_root

        self.snapshot_id = snapshot_id


def test_edit_repository() -> None:
    """Editing endpoint should return the proposed edits."""

    fake_service = FakeEditingService()

    app.dependency_overrides[
        get_editing_service
    ] = lambda: fake_service

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/editing/edit",
        json={
            "repository_root": ".",
            "instruction": "Rename foo to bar.",
        },
    )

    app.dependency_overrides.clear()

    assert (
        response.status_code
        == 200
    )

    assert (
        fake_service.request
        is not None
    )

    assert (
        fake_service.request.instruction
        == "Rename foo to bar."
    )

    assert response.json() == {
        "change_set": {
            "edits": [
                {
                    "relative_path": "main.py",
                    "original_content": "old",
                    "updated_content": "new",
                },
            ],
        },
    }


def test_apply_changes_returns_snapshot_id() -> None:
    """Apply endpoint should return the generated snapshot id."""

    fake_service = FakeEditingService()

    app.dependency_overrides[
        get_editing_service
    ] = lambda: fake_service

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/editing/apply",
        json={
            "repository_root": ".",
            "change_set": {
                "edits": [
                    {
                        "relative_path": "main.py",
                        "original_content": "old",
                        "updated_content": "new",
                    },
                ],
            },
        },
    )

    app.dependency_overrides.clear()

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "snapshot_id": "snapshot-1",
    }

    assert (
        fake_service.repository_root
        == Path(
            ".",
        )
    )

    assert (
        fake_service.change_set
        is not None
    )

    assert (
        fake_service.change_set.edits[0].relative_path
        == Path(
            "main.py",
        )
    )


def test_rollback_changes_delegates_and_returns_no_content() -> None:
    """Rollback endpoint should delegate and return HTTP 204."""

    fake_service = FakeEditingService()

    app.dependency_overrides[
        get_editing_service
    ] = lambda: fake_service

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/editing/rollback",
        json={
            "repository_root": ".",
            "snapshot_id": "snapshot-1",
        },
    )

    app.dependency_overrides.clear()

    assert (
        response.status_code
        == 204
    )

    assert (
        response.content
        == b""
    )

    assert (
        fake_service.repository_root
        == Path(
            ".",
        )
    )

    assert (
        fake_service.snapshot_id
        == "snapshot-1"
    )
