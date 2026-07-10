"""Chat domain models."""

from enum import StrEnum

from pydantic import BaseModel

from app.indexing.retrieval_models import SearchResult


class ChatRole(StrEnum):
    """Role of a chat message."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Provider-independent chat message."""

    role: ChatRole

    content: str


class ChatPrompt(BaseModel):
    """Provider-independent chat prompt."""

    messages: list[ChatMessage]


class ChatRequest(BaseModel):
    """Incoming chat request."""

    query: str


class ChatResponse(BaseModel):
    """Complete chat response."""

    content: str


class ChatChunk(BaseModel):
    """Streaming chat response fragment."""

    content: str

    is_final: bool


class ContextAssemblyRequest(BaseModel):
    """Input for Context Assembly."""

    query: str

    results: list[SearchResult]