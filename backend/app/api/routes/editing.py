"""Repository Editing endpoints."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status

from app.api.routes.editing_schemas import (
    ApplyRequest,
    ApplyResponse,
    RollbackRequest,
)
from app.dependencies.providers import (
    get_editing_service,
)
from app.editing.models import (
    EditRequest,
    EditResponse,
)
from app.editing.service import (
    EditingService,
)

router = APIRouter(
    prefix="/editing",
    tags=["Editing"],
)


@router.post(
    "/edit",
    response_model=EditResponse,
)
def edit_repository(
    request: EditRequest,
    editing_service: EditingService = Depends(
        get_editing_service,
    ),
) -> EditResponse:
    """Generate repository modifications."""

    return editing_service.edit(
        request,
    )


@router.post(
    "/apply",
    response_model=ApplyResponse,
)
def apply_changes(
    request: ApplyRequest,
    editing_service: EditingService = Depends(
        get_editing_service,
    ),
) -> ApplyResponse:
    """Apply a previously planned ChangeSet."""

    snapshot_id = editing_service.apply(
        repository_root=request.repository_root,
        change_set=request.change_set,
    )

    return ApplyResponse(
        snapshot_id=snapshot_id,
    )


@router.post(
    "/rollback",
    status_code=status.HTTP_204_NO_CONTENT,
)
def rollback_changes(
    request: RollbackRequest,
    editing_service: EditingService = Depends(
        get_editing_service,
    ),
) -> Response:
    """Restore files from a previously captured snapshot."""

    editing_service.rollback(
        repository_root=request.repository_root,
        snapshot_id=request.snapshot_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
