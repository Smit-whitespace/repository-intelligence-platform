"""Repository Editing endpoints."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status

from app.api.routes.editing_schemas import (
    ApplyRequest,
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
    status_code=status.HTTP_204_NO_CONTENT,
)
def apply_changes(
    request: ApplyRequest,
    editing_service: EditingService = Depends(
        get_editing_service,
    ),
) -> Response:
    """Apply a previously planned ChangeSet."""

    editing_service.apply(
        repository_root=request.repository_root,
        change_set=request.change_set,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )