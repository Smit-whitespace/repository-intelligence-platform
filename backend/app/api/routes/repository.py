"""Repository endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query

from app.dependencies.providers import get_repository_service
from app.repository.schemas import (
    RepositoryEntryResponse,
    RepositoryIndexResponse,
    RepositorySummaryResponse,
)
from app.repository.service import RepositoryService

router = APIRouter(
    prefix="/repository",
    tags=["Repository"],
)


@router.get(
    "/index",
    response_model=RepositoryIndexResponse,
)
def repository_index(
    root_directory: Path = Query(...),
    repository_service: RepositoryService = Depends(
        get_repository_service,
    ),
) -> RepositoryIndexResponse:
    """Return repository index."""

    index = repository_service.build_index(
        root_directory,
    )

    return RepositoryIndexResponse(
        summary=RepositorySummaryResponse(
            files=index.summary.files,
            directories=index.summary.directories,
            total_size_bytes=index.summary.total_size_bytes,
        ),
        entries=[
            RepositoryEntryResponse(
                name=entry.name,
                relative_path=entry.relative_path,
                is_directory=entry.is_directory,
                size_bytes=entry.size_bytes,
                modified_at=entry.modified_at,
                language=entry.language,
                sha256=entry.sha256,
                is_text_file=entry.is_text_file,
                mime_type=entry.mime_type,
            )
            for entry in index.entries
        ],
    )


@router.get(
    "/scan",
    response_model=list[RepositoryEntryResponse],
)
def repository_scan(
    root_directory: Path = Query(...),
    repository_service: RepositoryService = Depends(
        get_repository_service,
    ),
) -> list[RepositoryEntryResponse]:
    """Return repository entries."""

    return repository_index(
        root_directory,
        repository_service,
    ).entries


@router.get(
    "/summary",
    response_model=RepositorySummaryResponse,
)
def repository_summary(
    root_directory: Path = Query(...),
    repository_service: RepositoryService = Depends(
        get_repository_service,
    ),
) -> RepositorySummaryResponse:
    """Return repository summary."""

    return repository_index(
        root_directory,
        repository_service,
    ).summary