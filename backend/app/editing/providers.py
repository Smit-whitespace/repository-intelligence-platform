"""Repository Editing provider abstractions."""

from abc import ABC
from abc import abstractmethod

from app.editing.models import (
    EditRequest,
    EditResponse,
)


class EditingProvider(ABC):
    """Abstract repository editing provider."""

    @abstractmethod
    def edit(
        self,
        request: EditRequest,
    ) -> EditResponse:
        """Generate repository modifications."""