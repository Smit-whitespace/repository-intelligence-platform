"""Application exception handlers."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.chat.exceptions import ChatException
from app.core.storage.exceptions import StorageError
from app.editing.exceptions import (
    EditConflictError,
    EditingError,
    IncompleteRevertError,
    SnapshotNotFoundError,
    SnapshotPersistenceError,
    UnregisteredRepositoryError,
)
from app.indexing.exceptions import (
    IndexIncompatibleError,
    IndexingBusyError,
    IndexingError,
)
from app.projects.exceptions import (
    InvalidProjectError,
    ProjectNotFoundError,
)
from app.repository.exceptions import RepositoryScanError
from app.workspace.exceptions import (
    FileTooLargeError,
    NotATextFileError,
    UnregisteredWorkspaceError,
    WorkspaceError,
    WorkspaceFileNotFoundError,
)


_STATUS_BY_EXCEPTION: dict[type[Exception], int] = {
    UnregisteredRepositoryError: 403,
    EditConflictError: 409,
    IncompleteRevertError: 500,
    IndexIncompatibleError: 409,
    IndexingBusyError: 409,
    WorkspaceError: 400,
    UnregisteredWorkspaceError: 403,
    WorkspaceFileNotFoundError: 404,
    FileTooLargeError: 413,
    NotATextFileError: 415,
}
"""Specific subclasses that need a different status than their base.

Starlette resolves handlers along the exception's MRO, so these win over
the broader ``EditingError`` (400) and ``IndexingError`` (500) handlers
regardless of registration order.
"""


def register_exception_handlers(
    application: FastAPI,
) -> None:
    """Register application exception handlers."""

    for exception_type, status_code in _STATUS_BY_EXCEPTION.items():
        application.add_exception_handler(
            exception_type,
            _detail_handler(
                status_code,
            ),
        )

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


def _detail_handler(
    status_code: int,
):
    """Return a handler that reports the exception message as detail."""

    async def handle(
        request,
        exception: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": str(exception),
            },
        )

    return handle
