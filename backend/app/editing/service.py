"""Repository Editing service."""

from app.editing.models import (
    EditRequest,
    EditResponse,
)
from app.editing.providers import (
    EditingProvider,
)


class EditingService:
    """Repository Editing orchestration service."""

    def __init__(
        self,
        editing_provider: EditingProvider,
    ) -> None:
        """Initialize the editing service."""

        self._editing_provider = (
            editing_provider
        )

    def edit(
        self,
        request: EditRequest,
    ) -> EditResponse:
        """Generate repository modifications."""

        return self._editing_provider.edit(
            request,
        )