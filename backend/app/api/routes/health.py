"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class HealthResponse(BaseModel):
    """Application health response."""

    status: str = Field(
        description="Application health status.",
        examples=[
            "healthy",
        ],
    )

    application: str = Field(
        description="Application identifier.",
        examples=[
            "Repository Intelligence Platform (RIP)",
        ],
    )

    version: str = Field(
        description="Application version.",
        examples=[
            "0.1.0",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "application": "Repository Intelligence Platform (RIP)",
                "version": "0.1.0",
            },
        },
    )

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    response_model=HealthResponse,
    operation_id="getHealth",
    summary="Get API health",
    description="Return the backend health status and application version.",
    response_description="Current backend health status.",
)
def get_health() -> HealthResponse:
    """Return application health status."""

    return HealthResponse(
        status="healthy",
        application="Repository Intelligence Platform (RIP)",
        version="0.1.0",
    )
