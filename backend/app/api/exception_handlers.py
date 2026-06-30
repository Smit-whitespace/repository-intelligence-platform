"""Application exception handlers."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.storage.exceptions import StorageError
from app.projects.exceptions import (
    InvalidProjectError,
    ProjectNotFoundError,
)


def register_exception_handlers(
    application: FastAPI,
) -> None:
    """Register application exception handlers."""

    @application.exception_handler(
        InvalidProjectError,
    )
    async def handle_invalid_project(
        request,
        exception: InvalidProjectError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exception),
            },
        )

    @application.exception_handler(
        ProjectNotFoundError,
    )
    async def handle_project_not_found(
        request,
        exception: ProjectNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exception),
            },
        )

    @application.exception_handler(
        StorageError,
    )
    async def handle_storage_error(
        request,
        exception: StorageError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exception),
            },
        )