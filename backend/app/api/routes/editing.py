"""Repository Editing endpoints."""

from fastapi import APIRouter
from fastapi import Depends

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