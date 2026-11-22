"""Reusable OpenAPI response documentation."""

from typing import Any

from app.api.schemas import ErrorResponse

ResponseDocs = dict[int | str, dict[str, Any]]

BAD_REQUEST_RESPONSE: ResponseDocs = {
    400: {
        "model": ErrorResponse,
        "description": "The request is well-formed but cannot be processed.",
    },
}

NOT_FOUND_RESPONSE: ResponseDocs = {
    404: {
        "model": ErrorResponse,
        "description": "The requested resource was not found.",
    },
}

VALIDATION_ERROR_RESPONSE: ResponseDocs = {
    422: {
        "description": "Request validation failed.",
    },
}

SERVER_ERROR_RESPONSE: ResponseDocs = {
    500: {
        "model": ErrorResponse,
        "description": "The server failed while processing the request.",
    },
}

FORBIDDEN_RESPONSE: ResponseDocs = {
    403: {
        "model": ErrorResponse,
        "description": "The repository root is not a registered RIP project.",
    },
}

CONFLICT_RESPONSE: ResponseDocs = {
    409: {
        "model": ErrorResponse,
        "description": (
            "The request conflicts with the current state, such as an "
            "index built with a different embedding model."
        ),
    },
}

FILE_TOO_LARGE_RESPONSE: ResponseDocs = {
    413: {
        "model": ErrorResponse,
        "description": "The file exceeds the size limit for this tool.",
    },
}

NOT_TEXT_RESPONSE: ResponseDocs = {
    415: {
        "model": ErrorResponse,
        "description": "The file is binary or not valid UTF-8 text.",
    },
}
