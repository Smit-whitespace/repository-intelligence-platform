"""Chat endpoints."""

from collections.abc import Iterator

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi.responses import StreamingResponse

from app.api.response_docs import (
    SERVER_ERROR_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
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
    operation_id="chat",
    summary="Generate chat response",
    description="Generate a repository-aware chat response for a user query.",
    response_description="Generated chat response.",
    responses={
        **VALIDATION_ERROR_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(
        get_chat_service,
    ),
) -> ChatResponse:
    """Generate a repository-aware chat response."""

    import logging
    logging.warning("[INSTRUMENT] chat() called — query=%r, root_directory=%s", request.query, request.root_directory)

    response = chat_service.chat(
        models.ChatRequest(
            query=request.query,
            root_directory=request.root_directory,
        ),
    )

    return ChatResponse(
        content=response.content,
    )


@router.get(
    "/stream",
    operation_id="streamChat",
    summary="Stream chat response",
    description=(
        "Stream a repository-aware chat response using server-sent events."
    ),
    response_description="Server-sent event stream of chat content chunks.",
    responses={
        200: {
            "description": "Server-sent event stream.",
            "content": {
                "text/event-stream": {
                    "example": "data: Hello\n\ndata: World\n\n",
                },
            },
        },
        **VALIDATION_ERROR_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def stream_chat(
    query: str = Query(
        ...,
        description="User question to answer using repository context.",
        examples=[
            "Explain the editing workflow.",
        ],
    ),
    root_directory: str | None = Query(
        default=None,
        description="Active project root directory for scoping retrieval.",
        examples=[
            "/home/user/projects/my-project",
        ],
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
                    root_directory=root_directory,
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
