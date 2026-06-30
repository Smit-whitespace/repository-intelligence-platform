"""Project management endpoints."""

from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.dependencies.providers import (
    get_project_service,
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
)
def open_project(
    request: OpenProjectRequest,
    project_service: ProjectService = Depends(
        get_project_service,
    ),
) -> OpenProjectResponse:
    """Open a project."""

    project = project_service.open_project(
        request.root_directory,
    )

    return OpenProjectResponse(
        project=project.name,
        root_directory=project.root_directory,
    )


@router.get(
    "/info",
    response_model=ProjectInfoResponse,
)
def get_project_info(
    root_directory: Path = Query(
        ...,
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