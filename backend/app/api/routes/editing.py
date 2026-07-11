"""Repository Editing endpoints."""

from fastapi import APIRouter
from fastapi import Depends

from app.dependencies.providers import (
    get_editing_service,
)
from app.editing.models import (
    EditRequest,
)
from app.editing.schemas import (
    EditRepositoryRequest,
    EditRepositoryResponse,
    FileEditResponse,
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
    response_model=EditRepositoryResponse,
)
def edit_repository(
    request: EditRepositoryRequest,
    editing_service: EditingService = Depends(
        get_editing_service,
    ),
) -> EditRepositoryResponse:
    """Generate repository modifications."""

    response = editing_service.edit(
        EditRequest(
            instruction=request.instruction,
        ),
    )

    return EditRepositoryResponse(
        edits=[
            FileEditResponse(
                relative_path=edit.relative_path,
                original_content=edit.original_content,
                updated_content=edit.updated_content,
            )
            for edit in response.change_set.edits
        ],
    )