"""Default Repository Editing provider."""

from app.editing.models import (
    ChangeSet,
    EditRequest,
    EditResponse,
)
from app.editing.providers import (
    EditingProvider,
)


class DefaultEditingProvider(
    EditingProvider,
):
    """Default implementation of the Editing provider."""

    def edit(
        self,
        request: EditRequest,
    ) -> EditResponse:
        """Generate repository modifications."""

        return EditResponse(
            change_set=ChangeSet(
                edits=[],
            ),
        )