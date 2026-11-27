"""Persistence for the model configuration.

The configuration is per user, not per project: provider credentials and
model choices are personal, and a file inside a repository could be
committed by accident. It lives at ``~/.rip/models.json`` by
default (override with ``RIP_MODEL_CONFIG_PATH``). A home directory can
never be a RIP project, so this never collides with project storage.

Until a configuration is saved, the defaults come from the existing
``RIP_OLLAMA_*`` settings, so existing setups keep working unchanged.
"""

import json
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from app.core.config.models import OllamaSettings
from app.core.storage.locations import user_storage_directory
from app.llm.config import (
    ModelConfiguration,
    ModelRef,
    ProviderConfig,
    ProviderType,
)
from app.llm.exceptions import ModelConfigurationError

MODEL_CONFIG_FILE_NAME = "models.json"

DEFAULT_PROVIDER_NAME = "ollama"


def default_config_path() -> Path:
    """Return the per-user configuration file path."""

    return user_storage_directory() / MODEL_CONFIG_FILE_NAME


def configuration_from_ollama_settings(
    settings: OllamaSettings,
) -> ModelConfiguration:
    """Build the default configuration from the ``RIP_OLLAMA_*`` settings."""

    return ModelConfiguration(
        providers={
            DEFAULT_PROVIDER_NAME: ProviderConfig(
                type=ProviderType.OLLAMA,
                base_url=settings.base_url,
                timeout_seconds=settings.timeout_seconds,
            ),
        },
        primary=ModelRef(
            provider=DEFAULT_PROVIDER_NAME,
            model=settings.chat_model,
        ),
        embedding=ModelRef(
            provider=DEFAULT_PROVIDER_NAME,
            model=settings.embedding_model,
        ),
    )


class ModelConfigStore:
    """Load and save the model configuration file."""

    def __init__(
        self,
        path: Path,
        defaults: ModelConfiguration,
    ) -> None:
        self._path = path

        self._defaults = defaults

    @property
    def path(
        self,
    ) -> Path:
        return self._path

    def exists(
        self,
    ) -> bool:
        return self._path.is_file()

    def load(
        self,
    ) -> ModelConfiguration:
        """Return the saved configuration, or the defaults if none."""

        if not self._path.is_file():
            return self._defaults

        try:
            data = json.loads(
                self._path.read_text(
                    encoding="utf-8",
                ),
            )

            return ModelConfiguration.model_validate(
                data,
            )

        except (OSError, json.JSONDecodeError, ValidationError) as error:
            raise ModelConfigurationError(
                f"The model configuration at {self._path} is invalid: "
                f"{error}. Fix or delete the file to return to defaults.",
            ) from error

    def save(
        self,
        configuration: ModelConfiguration,
    ) -> None:
        """Write the configuration atomically."""

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = json.dumps(
            configuration.model_dump(
                mode="json",
            ),
            indent=2,
        ) + "\n"

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self._path.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(
                    temporary_file.name,
                )

                temporary_file.write(
                    payload,
                )

                temporary_file.flush()

                os.fsync(
                    temporary_file.fileno(),
                )

            temporary_path.replace(
                self._path,
            )

        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
