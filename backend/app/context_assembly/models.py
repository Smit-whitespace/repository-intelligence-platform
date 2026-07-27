"""Context Assembly domain models."""

from pydantic import BaseModel

from app.chat.models import ChatPrompt
from app.indexing.retrieval_models import SearchResult


class ContextAssemblyRequest(BaseModel):
    """Request for assembling chat context."""

    query: str

    results: list[SearchResult]


class ContextAssemblyResponse(BaseModel):
    """Result of context assembly."""

    prompt: ChatPrompt
