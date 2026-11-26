"""Ollama chat provider."""

from collections.abc import Iterator

import httpx
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

MAX_OUTPUT_TOKENS = 4_096
"""The most tokens one answer may use, thinking included.

Without a cap, a model that falls into a repetition loop writes until its
context window is full: on a laptop GPU that was over an hour for one
answer. 4,096 tokens is about 3,000 words, far longer than a useful answer.
"""

TRUNCATION_NOTE = (
    f"\n\n_[The answer was cut off at the {MAX_OUTPUT_TOKENS:,}-token limit.]_"
)


class OllamaChatProvider(
    ChatProvider,
):
    """Chat provider backed by Ollama."""

    def __init__(
        self,
        settings: OllamaSettings,
        model: str | None = None,
        base_url: str | None = None,
        think: bool | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        """Initialize the Ollama client.

        ``model``, ``base_url`` and ``timeout_seconds`` come from the model
        configuration; without them the ``LOC_OLLAMA_*`` settings apply.
        ``think`` turns a reasoning model's thinking on or off; ``None``
        leaves the model's default. The timeout is how long Ollama may stay
        silent, not how long an answer may take: answers are streamed, so
        it only fires when no token arrives for that long.
        """

        self._settings = settings

        self._model = model or settings.chat_model

        self._host = base_url or settings.base_url

        # None is left out of the request by the client (exclude_none), so
        # an unset value changes nothing for servers or models without it.
        self._think = think

        self._timeout_seconds = timeout_seconds or settings.timeout_seconds

        self._client = Client(
            host=self._host,
            timeout=self._timeout_seconds,
        )

    def generate(
        self,
        prompt: ChatPrompt,
    ) -> ChatResponse:
        """Generate a chat response using Ollama.

        Streams under the hood, so a long answer on a slow machine is not
        mistaken for a stalled server.
        """

        content = "".join(
            chunk.content
            for chunk in self.stream(
                prompt,
            )
        )

        if not content:
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
                think=self._think,
                options={
                    "num_predict": MAX_OUTPUT_TOKENS,
                },
            )

            for response in stream:
                content = response.message.content

                if content:
                    yield ChatChunk(
                        content=content,
                        is_final=False,
                    )

                # Say so when the cap cut the answer short, rather than
                # leaving a sentence hanging with no explanation.
                if response.done and response.done_reason == "length":
                    yield ChatChunk(
                        content=TRUNCATION_NOTE,
                        is_final=False,
                    )

        except ResponseError as error:
            raise ChatProviderError(
                str(
                    error,
                ),
            ) from error

        except httpx.TimeoutException as error:
            raise ChatProviderError(
                f"Ollama at {self._host} sent nothing for "
                f"{self._timeout_seconds:g} seconds. The model may still be "
                "loading or the machine may be overloaded; try again.",
            ) from error

        except (ConnectionError, httpx.HTTPError) as error:
            # The client raises the built-in ConnectionError when Ollama is
            # not running; left unhandled it became a bare HTTP 500.
            raise ChatProviderError(
                f"Could not reach Ollama at {self._host}. Is it running?",
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