"""Anthropic chat provider, using the official ``anthropic`` SDK.

System messages become the request's top-level ``system`` field; the
rest are passed as the conversation. Only text blocks are returned:
newer models also return thinking blocks, which are not part of the
answer.

A ``refusal`` stop reason is reported as an error. Anthropic's automatic
server-side fallback (re-running a refused request on another model) is
deliberately not enabled: RIP never switches models without the user
choosing to.
"""

from collections.abc import Iterator
from typing import Any

import anthropic

from app.chat.exceptions import ChatProviderError
from app.chat.models import (
    ChatChunk,
    ChatPrompt,
    ChatResponse,
    ChatRole,
)
from app.chat.providers import ChatProvider

MAX_OUTPUT_TOKENS = 16_000


class AnthropicChatProvider(
    ChatProvider,
):
    """Chat over Anthropic's Messages API."""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str | None = None,
        timeout_seconds: float = 120.0,
        client: Any | None = None,
    ) -> None:
        self._model = model

        self._client = client or anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )

    def generate(
        self,
        prompt: ChatPrompt,
    ) -> ChatResponse:
        """Return the complete response."""

        try:
            message = self._client.messages.create(
                **self._request(
                    prompt,
                ),
            )

        except anthropic.APIStatusError as error:
            raise ChatProviderError(
                f"Anthropic API error {error.status_code}: {error.message}",
            ) from error

        except anthropic.APIConnectionError as error:
            raise ChatProviderError(
                "Could not reach the Anthropic API.",
            ) from error

        self._raise_on_refusal(
            message,
        )

        return ChatResponse(
            content="".join(
                block.text
                for block in message.content
                if block.type == "text"
            ),
        )

    def stream(
        self,
        prompt: ChatPrompt,
    ) -> Iterator[ChatChunk]:
        """Yield text fragments as they are generated."""

        try:
            with self._client.messages.stream(
                **self._request(
                    prompt,
                ),
            ) as stream:
                for text in stream.text_stream:
                    if text:
                        yield ChatChunk(
                            content=text,
                            is_final=False,
                        )

                self._raise_on_refusal(
                    stream.get_final_message(),
                )

        except anthropic.APIStatusError as error:
            raise ChatProviderError(
                f"Anthropic API error {error.status_code}: {error.message}",
            ) from error

        except anthropic.APIConnectionError as error:
            raise ChatProviderError(
                "Could not reach the Anthropic API.",
            ) from error

    def _request(
        self,
        prompt: ChatPrompt,
    ) -> dict[str, Any]:
        system = "\n\n".join(
            message.content
            for message in prompt.messages
            if message.role is ChatRole.SYSTEM
        )

        request: dict[str, Any] = {
            "model": self._model,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "messages": [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in prompt.messages
                if message.role is not ChatRole.SYSTEM
            ],
        }

        if system:
            request["system"] = system

        return request

    @staticmethod
    def _raise_on_refusal(
        message: Any,
    ) -> None:
        if getattr(message, "stop_reason", None) != "refusal":
            return

        details = getattr(message, "stop_details", None)

        category = getattr(details, "category", None)

        raise ChatProviderError(
            "The model declined to answer"
            + (f" (category: {category})." if category else ".")
            + " RIP does not retry on another model automatically; "
            "choose a different model in Settings if this persists.",
        )
