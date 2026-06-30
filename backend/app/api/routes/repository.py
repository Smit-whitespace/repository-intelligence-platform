"""Repository endpoints."""

from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.dependencies.providers import (
    get_repository_service,
)
from app.repository.models import RepositoryEntry
from app.repository.service import RepositoryService

router = APIRouter(
    prefix="/repository",
    tags=["Repository"],
)


@router.get(
    "/scan",
    response_model=list[RepositoryEntry],
)
def scan_repository(
    root_directory: Path = Query(
        ...,
    ),
    repository_service: RepositoryService = Depends(
        get_repository_service,
    ),
) -> list[RepositoryEntry]:
    """Scan a repository."""

    return repository_service.scan(
        root_directory,
    )