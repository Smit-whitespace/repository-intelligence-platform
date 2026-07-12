"""Tests for the Editing service."""

from pathlib import Path

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


def test_edit() -> None:
    """Editing service should delegate to the provider."""

    provider = FakeEditingProvider()

    service = EditingService(
        editing_provider=provider,
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