"""Repository endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query

from app.api.response_docs import (
    BAD_REQUEST_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
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
    operation_id="getRepositoryIndex",
    summary="Get repository index",
    description=(
        "Scan a repository and return both aggregate summary data and "
        "individual file or directory entries."
    ),
    response_description="Repository index with summary and entries.",
    responses={
        **BAD_REQUEST_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
def repository_index(
    root_directory: Path = Query(
        ...,
        description="Absolute path to the repository root directory.",
        examples=[
            "A:/Personal Projects/Projects/local-openclaw",
        ],
    ),
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
    operation_id="scanRepository",
    summary="Scan repository",
    description="Scan a repository and return file and directory entries.",
    response_description="Repository file and directory entries.",
    responses={
        **BAD_REQUEST_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
def repository_scan(
    root_directory: Path = Query(
        ...,
        description="Absolute path to the repository root directory.",
        examples=[
            "A:/Personal Projects/Projects/local-openclaw",
        ],
    ),
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
    operation_id="getRepositorySummary",
    summary="Get repository summary",
    description="Scan a repository and return aggregate summary data.",
    response_description="Repository aggregate summary.",
    responses={
        **BAD_REQUEST_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
def repository_summary(
    root_directory: Path = Query(
        ...,
        description="Absolute path to the repository root directory.",
        examples=[
            "A:/Personal Projects/Projects/local-openclaw",
        ],
    ),
    repository_service: RepositoryService = Depends(
        get_repository_service,
    ),
) -> RepositorySummaryResponse:
    """Return repository summary."""

    return repository_index(
        root_directory,
        repository_service,
    ).summary
