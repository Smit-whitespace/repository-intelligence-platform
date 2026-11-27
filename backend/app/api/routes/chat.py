"""Chat endpoints."""

import json
import re
from collections.abc import Iterator
from pathlib import Path

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
    get_index_freshness,
)
from app.indexing.freshness import IndexFreshness
from app.indexing.models import FreshnessState

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
    index_freshness: IndexFreshness = Depends(
        get_index_freshness,
    ),
) -> ChatResponse:
    """Generate a repository-aware chat response."""

    # Update changed files first; ChatService itself never indexes.
    index = (
        index_freshness.refresh(
            Path(request.root_directory),
        )
        if request.root_directory
        else None
    )

    response = chat_service.chat(
        models.ChatRequest(
            query=request.query,
            root_directory=request.root_directory,
        ),
    )

    return ChatResponse(
        content=response.content,
        index=index,
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
                    "example": (
                        "event: index-progress\n"
                        'data: {"files": 3}\n\n'
                        "event: index\n"
                        'data: {"state": "updated", "changed_files": 3, '
                        '"added_files": 0, "removed_files": 0, '
                        '"updated_files": 3, "pending_files": 0, '
                        '"seconds": 1.2, "note": null}\n\n'
                        "data: Hello\n\ndata: World\n\n"
                    ),
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
    index_freshness: IndexFreshness = Depends(
        get_index_freshness,
    ),
) -> StreamingResponse:
    """Stream a repository-aware chat response."""

    chat_request = models.ChatRequest(
        query=query,
        root_directory=root_directory,
    )

    if not root_directory:
        return StreamingResponse(
            _stream_response(
                chat_service.stream(
                    chat_request,
                ),
            ),
            media_type="text/event-stream",
        )

    return StreamingResponse(
        _stream_fresh_response(
            chat_service,
            chat_request,
            index_freshness,
            Path(root_directory),
        ),
        media_type="text/event-stream",
    )


# Nothing changed, or nothing could be checked (the search path reports
# an unindexed or incompatible project itself).
_QUIET_STATES = frozenset(
    {
        FreshnessState.UP_TO_DATE,
        FreshnessState.NOT_INDEXED,
        FreshnessState.INCOMPATIBLE,
    },
)


def _stream_fresh_response(
    chat_service: ChatService,
    chat_request: models.ChatRequest,
    index_freshness: IndexFreshness,
    root: Path,
) -> Iterator[str]:
    """Update the index, report it with named events, then stream the answer.

    All of this runs inside the response iterator, so the headers are not
    delayed and the work stays off the event loop.
    """

    changes = index_freshness.changes(
        root,
    )

    if changes is not None and changes.total > 0:
        yield _named_event(
            "index-progress",
            json.dumps(
                {
                    "files": changes.total,
                },
            ),
        )

    result = index_freshness.refresh(
        root,
        changes,
    )

    if result.state not in _QUIET_STATES:
        yield _named_event(
            "index",
            result.model_dump_json(),
        )

    yield from _stream_response(
        chat_service.stream(
            chat_request,
        ),
    )


def _named_event(
    name: str,
    data: str,
) -> str:
    """Encode one named SSE event whose data is a single line of JSON."""

    return f"event: {name}\ndata: {data}\n\n"


def _stream_response(
    chunks: Iterator[models.ChatChunk],
) -> Iterator[str]:
    """Convert chat chunks into Server-Sent Events."""

    for chunk in chunks:
        yield _sse_event(
            chunk.content,
        )


def _sse_event(
    content: str,
) -> str:
    """Encode text as one SSE event, preserving line breaks.

    A line break inside a ``data:`` field ends that field, so multi-line
    content must be sent as one ``data:`` line per line; clients join
    them back with ``\\n``. Without this, a chunk containing a line
    break was cut off or split.
    """

    lines = re.split(
        r"\r\n|\r|\n",
        content,
    )

    return "".join(
        f"data: {line}\n"
        for line in lines
    ) + "\n"
