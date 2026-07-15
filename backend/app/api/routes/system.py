"""System readiness endpoints."""

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.api.routes.models import (
    _PROVIDER,
    _installed_models,
)
from app.core.config import settings as runtime_settings

APPLICATION_NAME = "Repository Intelligence Platform (RIP)"
APPLICATION_VERSION = "0.1.0"
API_VERSION = "v1"

router = APIRouter(
    prefix="/system",
    tags=["System"],
)


class SystemStatusResponse(BaseModel):
    """Frontend startup status response."""

    backend_health: str = Field(
        description="Backend health status.",
        examples=[
            "healthy",
        ],
    )

    provider_connectivity: str = Field(
        description="Configured provider connectivity status.",
        examples=[
            "available",
        ],
    )

    active_provider: str = Field(
        description="Active model provider.",
        examples=[
            _PROVIDER,
        ],
    )

    active_model: str = Field(
        description="Active chat model.",
        examples=[
            "qwen3:8b",
        ],
    )

    project_status: str = Field(
        description="Known project startup status.",
        examples=[
            "not_loaded",
        ],
    )

    repository_status: str = Field(
        description="Known repository startup status.",
        examples=[
            "not_loaded",
        ],
    )

    indexing_state: str = Field(
        description="Indexing subsystem startup state.",
        examples=[
            "available",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "backend_health": "healthy",
                "provider_connectivity": "available",
                "active_provider": _PROVIDER,
                "active_model": "qwen3.6",
                "project_status": "not_loaded",
                "repository_status": "not_loaded",
                "indexing_state": "available",
            },
        },
    )


class SystemCapabilitiesResponse(BaseModel):
    """Backend capability discovery response."""

    streaming: bool

    retrieval: bool

    editing: bool

    snapshots: bool

    rollback: bool

    providers: list[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "streaming": True,
                "retrieval": True,
                "editing": True,
                "snapshots": True,
                "rollback": True,
                "providers": [
                    _PROVIDER,
                ],
            },
        },
    )


class SystemVersionResponse(BaseModel):
    """Backend version response."""

    application_name: str

    application_version: str

    api_version: str

    backend_version: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "application_name": APPLICATION_NAME,
                "application_version": APPLICATION_VERSION,
                "api_version": API_VERSION,
                "backend_version": APPLICATION_VERSION,
            },
        },
    )


def _provider_connectivity() -> str:
    """Return provider connectivity without failing the status endpoint."""

    try:
        _installed_models()

    except HTTPException:
        return "unavailable"

    return "available"


@router.get(
    "/status",
    response_model=SystemStatusResponse,
    operation_id="getSystemStatus",
    summary="Get system status",
    description="Return frontend startup status for backend dependencies.",
    response_description="Backend startup status.",
)
def get_system_status() -> SystemStatusResponse:
    """Return system status."""

    return SystemStatusResponse(
        backend_health="healthy",
        provider_connectivity=_provider_connectivity(),
        active_provider=_PROVIDER,
        active_model=runtime_settings.settings.ollama.chat_model,
        project_status="not_loaded",
        repository_status="not_loaded",
        indexing_state="available",
    )


@router.get(
    "/capabilities",
    response_model=SystemCapabilitiesResponse,
    operation_id="getSystemCapabilities",
    summary="Get backend capabilities",
    description="Return backend capabilities for frontend feature detection.",
    response_description="Backend capabilities.",
)
def get_system_capabilities() -> SystemCapabilitiesResponse:
    """Return backend capabilities."""

    return SystemCapabilitiesResponse(
        streaming=True,
        retrieval=True,
        editing=True,
        snapshots=True,
        rollback=True,
        providers=[
            _PROVIDER,
        ],
    )


@router.get(
    "/version",
    response_model=SystemVersionResponse,
    operation_id="getSystemVersion",
    summary="Get backend version",
    description="Return application and API version information.",
    response_description="Backend version information.",
)
def get_system_version() -> SystemVersionResponse:
    """Return version information."""

    return SystemVersionResponse(
        application_name=APPLICATION_NAME,
        application_version=APPLICATION_VERSION,
        api_version=API_VERSION,
        backend_version=APPLICATION_VERSION,
    )
