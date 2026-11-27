"""Application exception handlers."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.chat.exceptions import ChatException
from app.core.storage.exceptions import StorageError
from app.editing.exceptions import (
    EditConflictError,
    EditingDisabledError,
    EditingError,
    IncompleteRevertError,
    ProposalNotFoundError,
    ProposalStateError,
    SnapshotNotFoundError,
    SnapshotPersistenceError,
    UnregisteredRepositoryError,
    UntrustedStateError,
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
from app.llm.exceptions import ModelConfigurationError
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
    ProposalNotFoundError: 404,
    ProposalStateError: 409,
    EditingDisabledError: 403,
    UntrustedStateError: 403,
    InvalidProjectError: 400,
    ProjectNotFoundError: 404,
    StorageError: 500,
    RepositoryScanError: 400,
    SnapshotNotFoundError: 404,
    SnapshotPersistenceError: 500,
    EditingError: 400,
    ChatException: 500,
    IndexingError: 500,
    IndexIncompatibleError: 409,
    IndexingBusyError: 409,
    ModelConfigurationError: 400,
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


UNEXPECTED_ERROR_DETAIL = "Internal Server Error"
"""What an unhandled exception returns (Starlette's own 500 body)."""


def error_status_and_detail(
    exception: Exception,
) -> tuple[int, str]:
    """The HTTP status and detail the registered handlers give an exception.

    Resolved along the exception's MRO like Starlette does; an exception
    with no handler is a 500 with a generic detail, never its message.
    """

    for exception_type in type(exception).__mro__:
        status_code = _STATUS_BY_EXCEPTION.get(exception_type)

        if status_code is not None:
            return status_code, str(exception)

    return 500, UNEXPECTED_ERROR_DETAIL


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
