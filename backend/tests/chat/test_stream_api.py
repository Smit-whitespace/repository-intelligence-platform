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


def test_multiline_chunks_are_encoded_as_one_event_per_chunk() -> None:
    """Line breaks inside a chunk must not split or truncate the event."""

    from app.api.routes.chat import _sse_event

    assert _sse_event("plain") == "data: plain\n\n"

    assert _sse_event("def f():\n    return 1") == (
        "data: def f():\ndata:     return 1\n\n"
    )

    assert _sse_event("a\r\nb\rc") == "data: a\ndata: b\ndata: c\n\n"

    # A chunk that is only a newline still reaches the client as "\n".
    assert _sse_event("\n") == "data: \ndata: \n\n"


def _parse_sse(
    stream: str,
) -> list[str]:
    """Decode an SSE stream the way a browser's EventSource does."""

    events: list[str] = []

    for block in stream.split("\n\n"):
        if not block:
            continue

        events.append(
            "\n".join(
                line[len("data: ") :]
                for line in block.split("\n")
                if line.startswith("data:")
            ),
        )

    return events


def test_multiline_chunks_round_trip_through_an_sse_parser() -> None:
    """What the client reassembles equals what the model streamed."""

    from app.api.routes.chat import _sse_event

    chunks = [
        "Here is code:\n",
        "```python\nprint('hi')\n```",
        " done",
    ]

    stream = "".join(
        _sse_event(chunk)
        for chunk in chunks
    )

    assert _parse_sse(stream) == chunks