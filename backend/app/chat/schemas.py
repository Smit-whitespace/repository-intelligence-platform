"""Chat API schemas."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Chat request."""

    query: str


class ChatResponse(BaseModel):
    """Chat response."""

    content: str