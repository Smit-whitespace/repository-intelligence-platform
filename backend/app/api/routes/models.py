"""Model management endpoints.

- ``GET /models`` lists models installed in the local Ollama server.
- ``GET`` / ``PUT /settings/model`` read and set the primary model from
  installed Ollama models (the Settings page's simple picker).
- ``GET`` / ``PUT /models/configuration`` read and replace the full
  model configuration (providers, primary, overrides, embedding).
- ``GET /models/effective`` shows which model each operation uses and
  which configuration level it came from.

All persistence and resolution logic lives in ``app.llm`` and the
dependency providers; these routes only translate requests.
"""

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from ollama import Client
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.api.response_docs import (
    BAD_REQUEST_RESPONSE,
    SERVER_ERROR_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.core.config import settings as runtime_settings
from app.dependencies import providers
from app.llm.config import (
    ModelConfiguration,
    ModelRef,
    ProviderType,
    Task,
)
from app.llm.resolver import EffectiveModel

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
        description="Provider of the model chat uses.",
        examples=[
            _PROVIDER,
        ],
    )

    active_model: str = Field(
        description="Model chat uses.",
        examples=[
            "qwen3:8b",
        ],
    )


class UpdateModelRequest(BaseModel):
    """Request to set the primary model to an installed Ollama model."""

    model: str = Field(
        description="Installed model to activate.",
        examples=[
            "qwen3:8b",
        ],
    )


class ModelConfigurationView(BaseModel):
    """The model configuration, plus where it lives and key status."""

    configuration: ModelConfiguration

    path: str = Field(
        description="Configuration file location.",
    )

    display_path: str = Field(
        description=(
            "The same location with the home folder written as ~, for "
            "showing on screen without revealing the user name."
        ),
    )

    saved: bool = Field(
        description="False while the defaults from LOC_OLLAMA_* are in use.",
    )

    api_keys_present: dict[str, bool] = Field(
        description="For each provider that names an API key variable, "
        "whether it is set. Key values are never returned.",
    )


class EffectiveModelsResponse(BaseModel):
    """Which model each operation uses."""

    models: list[EffectiveModel]


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


def active_chat_model() -> EffectiveModel:
    """Return the model chat answers use."""

    return providers.get_model_resolver().for_task(
        Task.CHAT_ANSWER,
    )


def _home_relative(
    path: Path,
) -> str:
    """``path`` with the home folder written as ``~`` (if it is inside it).

    Settings show this path on screen; the home folder contains the user
    name, which does not belong in screenshots or shared screens.
    """

    try:
        relative = path.expanduser().resolve().relative_to(
            Path.home().resolve(),
        )

    except (ValueError, RuntimeError, OSError):
        return str(path)

    return f"~/{relative.as_posix()}" if relative.parts else "~"


def _configuration_view() -> ModelConfigurationView:
    store = providers.get_model_config_store()

    configuration = providers.get_model_resolver().configuration

    return ModelConfigurationView(
        configuration=configuration,
        path=str(
            store.path,
        ),
        display_path=_home_relative(
            store.path,
        ),
        saved=store.exists(),
        api_keys_present={
            name: bool(
                os.environ.get(
                    provider.api_key_env,
                    "",
                ).strip(),
            )
            for name, provider in configuration.providers.items()
            if provider.api_key_env
        },
    )


@router.get(
    "/models",
    response_model=ModelsResponse,
    operation_id="listModels",
    summary="List installed models",
    description="Return models installed in the local Ollama server.",
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
    description="Return the model chat uses, as resolved from the configuration.",
    response_description="Active model configuration.",
)
def get_active_model() -> ActiveModelResponse:
    """Return the model chat uses."""

    effective = active_chat_model()

    return ActiveModelResponse(
        active_provider=effective.provider,
        active_model=effective.model,
    )


@router.put(
    "/settings/model",
    response_model=ActiveModelResponse,
    operation_id="updateActiveModel",
    summary="Update active model",
    description=(
        "Set the primary model to an installed Ollama model and save the "
        "configuration. Capability and task overrides still take "
        "precedence where they are configured."
    ),
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
    """Set the primary model to an installed Ollama model."""

    installed_model_names = {
        model.name
        for model in _installed_models()
    }

    if request.model not in installed_model_names:
        raise HTTPException(
            status_code=400,
            detail="Requested model is not installed.",
        )

    configuration = providers.get_model_resolver().configuration

    ollama_provider = next(
        (
            name
            for name, provider in configuration.providers.items()
            if provider.type is ProviderType.OLLAMA
        ),
        None,
    )

    if ollama_provider is None:
        raise HTTPException(
            status_code=400,
            detail="No Ollama provider is configured; edit the model "
            "configuration instead.",
        )

    providers.apply_model_configuration(
        configuration.model_copy(
            update={
                "primary": ModelRef(
                    provider=ollama_provider,
                    model=request.model,
                ),
            },
        ),
    )

    effective = active_chat_model()

    return ActiveModelResponse(
        active_provider=effective.provider,
        active_model=effective.model,
    )


@router.get(
    "/models/configuration",
    response_model=ModelConfigurationView,
    operation_id="getModelConfiguration",
    summary="Get model configuration",
    description=(
        "Return the full model configuration: providers, primary model, "
        "capability and task overrides, and the embedding model. API key "
        "values are never returned, only whether each is set."
    ),
    response_description="Model configuration.",
    responses={
        **BAD_REQUEST_RESPONSE,
    },
)
def get_model_configuration() -> ModelConfigurationView:
    """Return the model configuration."""

    return _configuration_view()


@router.put(
    "/models/configuration",
    response_model=ModelConfigurationView,
    operation_id="updateModelConfiguration",
    summary="Replace model configuration",
    description=(
        "Validate and save a complete model configuration. Takes effect "
        "on the next request. Changing the embedding model does not "
        "reindex: semantic search reports the mismatch until you reindex."
    ),
    response_description="Saved model configuration.",
    responses={
        **BAD_REQUEST_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
def update_model_configuration(
    configuration: ModelConfiguration,
) -> ModelConfigurationView:
    """Save a new model configuration."""

    providers.apply_model_configuration(
        configuration,
    )

    return _configuration_view()


@router.get(
    "/models/effective",
    response_model=EffectiveModelsResponse,
    operation_id="getEffectiveModels",
    summary="Get effective models",
    description=(
        "Return the model each operation uses and the configuration level "
        "it came from (task, capability, primary or embedding)."
    ),
    response_description="Effective model per operation.",
    responses={
        **BAD_REQUEST_RESPONSE,
    },
)
def get_effective_models() -> EffectiveModelsResponse:
    """Return the effective model for every operation."""

    return EffectiveModelsResponse(
        models=providers.get_model_resolver().effective_models(),
    )
