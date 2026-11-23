"""OpenAI-compatible chat and embedding providers.

One adapter for every API that speaks ``POST {base_url}/chat/completions``
and ``POST {base_url}/embeddings``: OpenAI, OpenRouter, LM Studio, vLLM,
Ollama's ``/v1`` endpoint, and Gemini's OpenAI-compatible endpoint.

Errors never include the API key. Responses are parsed defensively,
because "compatible" servers differ in the details.
"""

import json
from collections.abc import Iterator, Sequence
from typing import Any

import httpx

from app.chat.exceptions import ChatProviderError
from app.chat.models import (
    ChatChunk,
    ChatPrompt,
    ChatResponse,
)
from app.chat.providers import ChatProvider
from app.indexing.exceptions import EmbeddingError
from app.indexing.models import EmbeddingVector
from app.indexing.providers import EmbeddingProvider

_ERROR_BODY_LIMIT = 300


def _headers(
    api_key: str | None,
) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    return headers


def _describe_status_error(
    response: httpx.Response,
) -> str:
    """Summarize an error response without echoing request headers."""

    try:
        body = response.read().decode(
            "utf-8",
            errors="replace",
        )

    except httpx.HTTPError:
        body = ""

    return (
        f"Provider returned HTTP {response.status_code}: "
        f"{body[:_ERROR_BODY_LIMIT]}"
    ).rstrip(": ")


class OpenAICompatibleChatProvider(
    ChatProvider,
):
    """Chat over an OpenAI-compatible ``/chat/completions`` API."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None,
        timeout_seconds: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._url = f"{base_url.rstrip('/')}/chat/completions"

        self._model = model

        self._client = client or httpx.Client(
            timeout=timeout_seconds,
            headers=_headers(
                api_key,
            ),
        )

    def generate(
        self,
        prompt: ChatPrompt,
    ) -> ChatResponse:
        """Return the complete response."""

        try:
            response = self._client.post(
                self._url,
                json=self._body(
                    prompt,
                    stream=False,
                ),
            )

        except httpx.RequestError as error:
            raise ChatProviderError(
                f"Could not reach the model provider at {self._url}: {error}",
            ) from error

        if response.is_error:
            raise ChatProviderError(
                _describe_status_error(
                    response,
                ),
            )

        try:
            content = response.json()["choices"][0]["message"]["content"]

        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise ChatProviderError(
                "The model provider returned an unexpected response shape.",
            ) from error

        if not isinstance(content, str):
            raise ChatProviderError(
                "The model provider returned a response with no text.",
            )

        return ChatResponse(
            content=content,
        )

    def stream(
        self,
        prompt: ChatPrompt,
    ) -> Iterator[ChatChunk]:
        """Yield text fragments as server-sent events arrive."""

        try:
            with self._client.stream(
                "POST",
                self._url,
                json=self._body(
                    prompt,
                    stream=True,
                ),
            ) as response:
                if response.is_error:
                    raise ChatProviderError(
                        _describe_status_error(
                            response,
                        ),
                    )

                for line in response.iter_lines():
                    done, text = self._parse_event(
                        line,
                    )

                    if done:
                        return

                    if text:
                        yield ChatChunk(
                            content=text,
                            is_final=False,
                        )

        except httpx.RequestError as error:
            raise ChatProviderError(
                f"Could not reach the model provider at {self._url}: {error}",
            ) from error

    def _body(
        self,
        prompt: ChatPrompt,
        stream: bool,
    ) -> dict[str, Any]:
        return {
            "model": self._model,
            "messages": [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in prompt.messages
            ],
            "stream": stream,
        }

    @staticmethod
    def _parse_event(
        line: str,
    ) -> tuple[bool, str | None]:
        """Parse one SSE line into (stream is done, text delta)."""

        if not line.startswith("data:"):
            return False, None

        data = line[len("data:") :].strip()

        if data == "[DONE]":
            return True, None

        try:
            event = json.loads(
                data,
            )

            content = event["choices"][0]["delta"].get("content")

        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            return False, None

        return False, content if isinstance(content, str) else None


class OpenAICompatibleEmbeddingProvider(
    EmbeddingProvider,
):
    """Embeddings over an OpenAI-compatible ``/embeddings`` API."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None,
        timeout_seconds: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")

        self._url = f"{self._base_url}/embeddings"

        self._model = model

        self._client = client or httpx.Client(
            timeout=timeout_seconds,
            headers=_headers(
                api_key,
            ),
        )

    @property
    def identity(
        self,
    ) -> str:
        """Endpoint plus model: the same model name on another server may
        be a different model, so both identify the vectors."""

        return f"openai_compatible:{self._base_url}:{self._model}"

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Embed texts, preserving input order."""

        try:
            response = self._client.post(
                self._url,
                json={
                    "model": self._model,
                    "input": list(
                        texts,
                    ),
                },
            )

        except httpx.RequestError as error:
            raise EmbeddingError(
                f"Could not reach the embedding provider at {self._url}: {error}",
            ) from error

        if response.is_error:
            raise EmbeddingError(
                _describe_status_error(
                    response,
                ),
            )

        try:
            items = sorted(
                response.json()["data"],
                key=lambda item: item["index"],
            )

            return [
                EmbeddingVector(
                    values=[
                        float(value)
                        for value in item["embedding"]
                    ],
                )
                for item in items
            ]

        except (ValueError, KeyError, TypeError) as error:
            raise EmbeddingError(
                "The embedding provider returned an unexpected response shape.",
            ) from error
