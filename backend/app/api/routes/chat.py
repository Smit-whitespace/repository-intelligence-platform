"""Chat endpoints."""

from collections.abc import Iterator

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi.responses import StreamingResponse

from app.chat import models
from app.chat.schemas import (
    ChatRequest,
    ChatResponse,
)
from app.chat.service import ChatService
from app.dependencies.providers import (
    get_chat_service,
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(
        get_chat_service,
    ),
) -> ChatResponse:
    """Generate a repository-aware chat response."""

    response = chat_service.chat(
        models.ChatRequest(
            query=request.query,
        ),
    )

    return ChatResponse(
        content=response.content,
    )


@router.get(
    "/stream",
)
def stream_chat(
    query: str = Query(
        ...,
    ),
    chat_service: ChatService = Depends(
        get_chat_service,
    ),
) -> StreamingResponse:
    """Stream a repository-aware chat response."""

    return StreamingResponse(
        _stream_response(
            chat_service.stream(
                models.ChatRequest(
                    query=query,
                ),
            ),
        ),
        media_type="text/event-stream",
    )


def _stream_response(
    chunks: Iterator[models.ChatChunk],
) -> Iterator[str]:
    """Convert chat chunks into Server-Sent Events."""

    for chunk in chunks:
        yield f"data: {chunk.content}\n\n"