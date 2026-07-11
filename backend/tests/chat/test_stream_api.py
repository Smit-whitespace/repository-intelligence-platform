"""Tests for chat streaming API."""

from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.chat.models import (
    ChatChunk,
    ChatRequest,
)
from app.dependencies.providers import (
    get_chat_service,
)
from app.main import app


class FakeChatService:
    """Fake chat service."""

    def __init__(
        self,
    ) -> None:
        """Initialize the fake chat service."""

        self.request: ChatRequest | None = (
            None
        )

    def stream(
        self,
        request: ChatRequest,
    ) -> Iterator[ChatChunk]:
        """Return a deterministic stream."""

        self.request = request

        yield ChatChunk(
            content="Hello",
            is_final=False,
        )

        yield ChatChunk(
            content="World",
            is_final=False,
        )

        yield ChatChunk(
            content="!",
            is_final=True,
        )


def test_chat_stream() -> None:
    """Streaming endpoint should produce valid SSE output."""

    fake_service = FakeChatService()

    app.dependency_overrides[
        get_chat_service
    ] = lambda: fake_service

    client = TestClient(
        app,
    )

    with client.stream(
        "GET",
        "/api/v1/chat/stream",
        params={
            "query": "Explain main.py",
        },
    ) as response:
        assert (
            response.status_code
            == 200
        )

        assert (
            "text/event-stream"
            in response.headers[
                "content-type"
            ]
        )

        stream = "".join(
            response.iter_text(),
        )

    app.dependency_overrides.clear()

    assert (
        fake_service.request
        is not None
    )

    assert (
        fake_service.request.query
        == "Explain main.py"
    )

    assert (
        stream
        == (
            "data: Hello\n\n"
            "data: World\n\n"
            "data: !\n\n"
        )
    )