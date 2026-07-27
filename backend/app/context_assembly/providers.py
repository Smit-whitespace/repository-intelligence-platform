"""Context Assembly abstractions."""

from abc import ABC
from abc import abstractmethod

from app.context_assembly.models import (
    ContextAssemblyRequest,
    ContextAssemblyResponse,
)


class ContextAssembly(ABC):
    """Abstract Context Assembly service."""

    @abstractmethod
    def assemble(
        self,
        request: ContextAssemblyRequest,
    ) -> ContextAssemblyResponse:
        """Assemble repository context into a chat prompt."""
