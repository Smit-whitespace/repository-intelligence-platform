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
        "edits": [
            {
                "relative_path": "main.py",
                "original_content": "old",
                "updated_content": "new",
            },
        ],
    }