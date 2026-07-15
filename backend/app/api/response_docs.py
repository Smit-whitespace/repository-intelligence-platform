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
