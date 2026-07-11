"""Tests for chat API endpoints."""

from fastapi.testclient import TestClient

from app.chat.models import (
    ChatRequest,
    ChatResponse,
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

    def chat(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """Return a deterministic response."""

        self.request = request

        return ChatResponse(
            content="Hello from test.",
        )


def test_chat() -> None:
    """Chat endpoint should return a response."""

    fake_service = FakeChatService()

    app.dependency_overrides[
        get_chat_service
    ] = lambda: fake_service

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "query": "Explain main.py",
        },
    )

    app.dependency_overrides.clear()

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "content": "Hello from test.",
    }

    assert (
        fake_service.request
        is not None
    )

    assert (
        fake_service.request.query
        == "Explain main.py"
    )