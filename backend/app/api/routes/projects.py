"""Project management endpoints."""

from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.api.response_docs import (
    BAD_REQUEST_RESPONSE,
    NOT_FOUND_RESPONSE,
    SERVER_ERROR_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.dependencies.providers import (
    get_project_initialization_service,
    get_project_service,
)
from app.projects.initialization_service import (
    ProjectInitializationService,
)
from app.projects.schemas import (
    OpenProjectRequest,
    OpenProjectResponse,
    ProjectInfoResponse,
)
from app.projects.service import (
    ProjectService,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post(
    "/open",
    response_model=OpenProjectResponse,
    operation_id="openProject",
    summary="Open project",
    description=("Validate a project root directory and persist RIP project metadata."),
    response_description="Opened project metadata.",
    responses={
        **BAD_REQUEST_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def open_project(
    request: OpenProjectRequest,
    initialization_service: ProjectInitializationService = Depends(
        get_project_initialization_service,
    ),
) -> OpenProjectResponse:
    """Open a project."""

    project, diagnostics = initialization_service.open_project(
        request.root_directory,
    )

    return OpenProjectResponse(
        project=project.name,
        root_directory=project.root_directory,
        indexing_diagnostics=diagnostics,
    )


@router.get(
    "/info",
    response_model=ProjectInfoResponse,
    operation_id="getProjectInfo",
    summary="Get project info",
    description="Return persisted RIP project metadata.",
    response_description="Persisted project metadata.",
    responses={
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def get_project_info(
    root_directory: Path = Query(
        ...,
        description="Absolute path to the project root directory.",
        examples=[
            "/home/user/projects/my-project",
        ],
    ),
    project_service: ProjectService = Depends(
        get_project_service,
    ),
) -> ProjectInfoResponse:
    """Return project metadata."""

    project = project_service.get_project(
        root_directory,
    )

    return ProjectInfoResponse(
        name=project.name,
        root_directory=project.root_directory,
        storage_directory=project.storage_directory,
        created_at=project.created_at,
    )
