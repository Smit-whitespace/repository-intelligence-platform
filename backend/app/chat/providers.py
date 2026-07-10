"""Chat provider abstractions."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Iterator

from app.chat.models import (
    ChatChunk,
    ChatPrompt,
    ChatResponse,
)


class ChatProvider(ABC):
    """Abstract chat provider."""

    @abstractmethod
    def generate(
        self,
        prompt: ChatPrompt,
    ) -> ChatResponse:
        """Generate a chat response."""

    @abstractmethod
    def stream(
        self,
        prompt: ChatPrompt,
    ) -> Iterator[ChatChunk]:
        """Stream a chat response."""