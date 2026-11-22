"""Ollama chat provider."""

from collections.abc import Iterator

from ollama import Client
from ollama import ResponseError

from app.chat.exceptions import ChatProviderError
from app.chat.models import (
    ChatChunk,
    ChatMessage,
    ChatPrompt,
    ChatResponse,
)
from app.chat.providers import ChatProvider
from app.core.config.models import OllamaSettings


class OllamaChatProvider(
    ChatProvider,
):
    """Chat provider backed by Ollama."""

    def __init__(
        self,
        settings: OllamaSettings,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the Ollama client.

        ``model`` and ``base_url`` come from the model configuration;
        without them the ``LOC_OLLAMA_*`` settings apply.
        """

        self._settings = settings

        self._model = model or settings.chat_model

        self._client = Client(
            host=base_url or settings.base_url,
        )

    def generate(
        self,
        prompt: ChatPrompt,
    ) -> ChatResponse:
        """Generate a chat response using Ollama."""

        try:
            response = self._client.chat(
                model=self._model,
                messages=self._build_messages(
                    prompt,
                ),
            )

        except ResponseError as error:
            raise ChatProviderError(
                str(
                    error,
                ),
            ) from error

        content = response.message.content

        if content is None:
            raise ChatProviderError(
                "Ollama returned a chat response with no content.",
            )

        return ChatResponse(
            content=content,
        )

    def stream(
        self,
        prompt: ChatPrompt,
    ) -> Iterator[ChatChunk]:
        """Stream a chat response using Ollama."""

        try:
            stream = self._client.chat(
                model=self._model,
                messages=self._build_messages(
                    prompt,
                ),
                stream=True,
            )

            for response in stream:
                content = response.message.content

                if content is None:
                    continue

                yield ChatChunk(
                    content=content,
                    is_final=False,
                )

        except ResponseError as error:
            raise ChatProviderError(
                str(
                    error,
                ),
            ) from error

    def _build_messages(
        self,
        prompt: ChatPrompt,
    ) -> list[dict[str, str]]:
        """Convert a chat prompt into Ollama messages."""

        return [
            self._build_message(
                message,
            )
            for message in prompt.messages
        ]

    def _build_message(
        self,
        message: ChatMessage,
    ) -> dict[str, str]:
        """Convert a chat message into an Ollama message."""

        return {
            "role": message.role.value,
            "content": message.content,
        }