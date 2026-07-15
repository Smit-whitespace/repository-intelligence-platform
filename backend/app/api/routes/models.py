"""Model management endpoints."""

from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from ollama import Client

from app.api.response_docs import (
    BAD_REQUEST_RESPONSE,
    SERVER_ERROR_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.core.config import settings as runtime_settings
from app.core.config.provider import persist_chat_model
from app.dependencies import providers
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

router = APIRouter(
    tags=["Models"],
)

_PROVIDER = "ollama"


class ModelInfo(BaseModel):
    """Frontend-safe model information."""

    provider: str = Field(
        description="Model provider identifier.",
        examples=[
            _PROVIDER,
        ],
    )

    name: str = Field(
        description="Installed model name.",
        examples=[
            "qwen3:8b",
        ],
    )


class ModelsResponse(BaseModel):
    """Installed model list response."""

    models: list[ModelInfo]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "models": [
                    {
                        "provider": _PROVIDER,
                        "name": "qwen3:8b",
                    },
                ],
            },
        },
    )


class ActiveModelResponse(BaseModel):
    """Active model response."""

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


class UpdateModelRequest(BaseModel):
    """Request to update the active chat model."""

    model: str = Field(
        description="Installed model to activate.",
        examples=[
            "qwen3:8b",
        ],
    )


def _ollama_client() -> Client:
    """Create an Ollama client from configured settings."""

    return Client(
        host=runtime_settings.settings.ollama.base_url,
    )


def _model_name(
    model: Any,
) -> str | None:
    """Extract a model name from an Ollama model object."""

    if isinstance(
        model,
        dict,
    ):
        value = model.get(
            "model",
        ) or model.get(
            "name",
        )

    else:
        value = getattr(
            model,
            "model",
            None,
        ) or getattr(
            model,
            "name",
            None,
        )

    if isinstance(
        value,
        str,
    ):
        return value

    return None


def _installed_models() -> list[ModelInfo]:
    """Return installed Ollama models in frontend-safe form."""

    try:
        response = _ollama_client().list()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Failed to query model provider.",
        ) from error

    raw_models = getattr(
        response,
        "models",
        [],
    )

    models = [
        ModelInfo(
            provider=_PROVIDER,
            name=name,
        )
        for model in raw_models
        if (
            name := _model_name(
                model,
            )
        )
    ]

    return sorted(
        models,
        key=lambda model: model.name,
    )


@router.get(
    "/models",
    response_model=ModelsResponse,
    operation_id="listModels",
    summary="List installed models",
    description="Return installed chat models from the configured provider.",
    response_description="Installed models.",
    responses={
        **SERVER_ERROR_RESPONSE,
    },
)
def list_models() -> ModelsResponse:
    """Return installed models."""

    return ModelsResponse(
        models=_installed_models(),
    )


@router.get(
    "/settings/model",
    response_model=ActiveModelResponse,
    operation_id="getActiveModel",
    summary="Get active model",
    description="Return the configured active chat model.",
    response_description="Active model configuration.",
)
def get_active_model() -> ActiveModelResponse:
    """Return the active chat model."""

    return ActiveModelResponse(
        active_provider=_PROVIDER,
        active_model=runtime_settings.settings.ollama.chat_model,
    )


@router.put(
    "/settings/model",
    response_model=ActiveModelResponse,
    operation_id="updateActiveModel",
    summary="Update active model",
    description="Validate and persist the active chat model.",
    response_description="Updated active model configuration.",
    responses={
        **BAD_REQUEST_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def update_active_model(
    request: UpdateModelRequest,
) -> ActiveModelResponse:
    """Update the active chat model."""

    installed_model_names = {
        model.name
        for model in _installed_models()
    }

    if request.model not in installed_model_names:
        raise HTTPException(
            status_code=400,
            detail="Requested model is not installed.",
        )

    persist_chat_model(
        request.model,
    )

    runtime_settings.settings.ollama.chat_model = (
        request.model
    )

    providers.get_chat_provider.cache_clear()
    providers.get_chat_service.cache_clear()

    return ActiveModelResponse(
        active_provider=_PROVIDER,
        active_model=request.model,
    )
