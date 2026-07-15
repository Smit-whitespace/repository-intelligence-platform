"""Application exception handlers."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.chat.exceptions import ChatException
from app.core.storage.exceptions import StorageError
from app.editing.exceptions import (
    EditingError,
    SnapshotNotFoundError,
    SnapshotPersistenceError,
)
from app.indexing.exceptions import IndexingError
from app.projects.exceptions import (
    InvalidProjectError,
    ProjectNotFoundError,
)
from app.repository.exceptions import RepositoryScanError


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

    @application.exception_handler(
        RepositoryScanError,
    )
    async def handle_repository_scan_error(
        request,
        exception: RepositoryScanError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exception),
            },
        )

    @application.exception_handler(
        SnapshotNotFoundError,
    )
    async def handle_snapshot_not_found(
        request,
        exception: SnapshotNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exception),
            },
        )

    @application.exception_handler(
        SnapshotPersistenceError,
    )
    async def handle_snapshot_persistence_error(
        request,
        exception: SnapshotPersistenceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exception),
            },
        )

    @application.exception_handler(
        EditingError,
    )
    async def handle_editing_error(
        request,
        exception: EditingError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exception),
            },
        )

    @application.exception_handler(
        ChatException,
    )
    async def handle_chat_error(
        request,
        exception: ChatException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exception),
            },
        )

    @application.exception_handler(
        IndexingError,
    )
    async def handle_indexing_error(
        request,
        exception: IndexingError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exception),
            },
        )
