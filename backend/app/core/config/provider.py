"""Configuration provider implementations."""

import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.models import (
    ApplicationSettings,
    ChromaSettings,
    IndexingSettings,
    ModelsSettings,
    SecuritySettings,
    LoggingSettings,
    OllamaSettings,
    ServerSettings,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[4]

_ENV_FILE = _PROJECT_ROOT / ".env"

ENVIRONMENT_PREFIX = "RIP_"

LEGACY_ENVIRONMENT_PREFIX = "LOC_"
"""The prefix until Sprint 14, from the project's working title (Local
OpenClaw). Still read, with a warning, so existing ``.env`` files and
scripts keep working (ADR-0021)."""

logger = logging.getLogger(__name__)


class EnvironmentSettings(BaseSettings):
    """Environment-backed application settings."""

    model_config = SettingsConfigDict(
        env_prefix=ENVIRONMENT_PREFIX,
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server_host: str = "127.0.0.1"

    server_port: int = 8000

    server_allowed_hosts: str = "localhost,127.0.0.1"
    """Comma-separated Host header values the API accepts."""

    server_frontend_url: str = "http://localhost:5173"

    logging_level: str = "INFO"

    logging_json_logs: bool = False

    ollama_base_url: str = "http://localhost:11434"

    ollama_embedding_model: str = "nomic-embed-text"

    ollama_chat_model: str = "qwen3:8b"

    ollama_timeout_seconds: int = 120

    chroma_collection_name: str = "repository_chunks"

    model_config_path: str = ""

    integrity_key_path: str = ""

    api_token_path: str = ""

    indexing_chunk_size: int = 512

    indexing_chunk_overlap: int = 64

    indexing_refresh_seconds: int = 15


class _LegacyEnvironmentSettings(EnvironmentSettings):
    """The same settings under the former ``LOC_`` prefix."""

    model_config = SettingsConfigDict(
        env_prefix=LEGACY_ENVIRONMENT_PREFIX,
    )


def read_environment(
    env_file: Path | None = _ENV_FILE,
) -> EnvironmentSettings:
    """Read settings from ``RIP_*`` variables, falling back to ``LOC_*``.

    A ``RIP_`` value always wins. A setting given only under its former
    ``LOC_`` name is used, and a warning names the variable to rename.
    """

    current = EnvironmentSettings(
        _env_file=env_file,  # type: ignore[call-arg]
    )

    legacy = _LegacyEnvironmentSettings(
        _env_file=env_file,  # type: ignore[call-arg]
    )

    carried = sorted(
        legacy.model_fields_set - current.model_fields_set,
    )

    for field in carried:
        logger.warning(
            "%s%s is deprecated; rename it to %s%s",
            LEGACY_ENVIRONMENT_PREFIX,
            field.upper(),
            ENVIRONMENT_PREFIX,
            field.upper(),
        )

    return current.model_copy(
        update={
            field: getattr(legacy, field)
            for field in carried
        },
    )


@lru_cache(maxsize=1)
def get_settings() -> ApplicationSettings:
    """Return cached application settings."""

    environment = read_environment()

    return ApplicationSettings(
        server=ServerSettings(
            host=environment.server_host,
            port=environment.server_port,
            allowed_hosts=[
                host.strip()
                for host in environment.server_allowed_hosts.split(",")
                if host.strip()
            ],
            frontend_url=environment.server_frontend_url,
        ),
        logging=LoggingSettings(
            level=environment.logging_level,
            json_logs=environment.logging_json_logs,
        ),
        ollama=OllamaSettings(
            base_url=environment.ollama_base_url,
            embedding_model=environment.ollama_embedding_model,
            chat_model=environment.ollama_chat_model,
            timeout_seconds=environment.ollama_timeout_seconds,
        ),
        models=ModelsSettings(
            config_path=environment.model_config_path,
        ),
        security=SecuritySettings(
            integrity_key_path=environment.integrity_key_path,
            api_token_path=environment.api_token_path,
        ),
        chroma=ChromaSettings(
            collection_name=environment.chroma_collection_name,
        ),
        indexing=IndexingSettings(
            chunk_size=environment.indexing_chunk_size,
            chunk_overlap=environment.indexing_chunk_overlap,
            refresh_seconds=environment.indexing_refresh_seconds,
        ),
    )
