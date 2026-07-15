"""Configuration provider implementations."""

from functools import lru_cache
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.models import (
    ApplicationSettings,
    ChromaSettings,
    IndexingSettings,
    LoggingSettings,
    OllamaSettings,
    ServerSettings,
    StorageSettings,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[4]

_ENV_FILE = _PROJECT_ROOT / ".env"

_CHAT_MODEL_ENV_KEY = "LOC_OLLAMA_CHAT_MODEL"


class EnvironmentSettings(BaseSettings):
    """Environment-backed application settings."""

    model_config = SettingsConfigDict(
        env_prefix="LOC_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server_host: str = "127.0.0.1"

    server_port: int = 8000

    logging_level: str = "INFO"

    logging_json_logs: bool = False

    storage_root_directory: Path = Path(
        ".local_openclaw",
    )

    ollama_base_url: str = "http://localhost:11434"

    ollama_embedding_model: str = "nomic-embed-text"

    ollama_chat_model: str = "qwen3:8b"

    ollama_timeout_seconds: int = 120

    chroma_persist_directory: Path = Path(
        ".local_openclaw/index/chroma",
    )

    chroma_collection_name: str = "repository_chunks"

    indexing_chunk_size: int = 512

    indexing_chunk_overlap: int = 64


@lru_cache(maxsize=1)
def get_settings() -> ApplicationSettings:
    """Return cached application settings."""

    environment = EnvironmentSettings()

    return ApplicationSettings(
        server=ServerSettings(
            host=environment.server_host,
            port=environment.server_port,
        ),
        logging=LoggingSettings(
            level=environment.logging_level,
            json_logs=environment.logging_json_logs,
        ),
        storage=StorageSettings(
            root_directory=environment.storage_root_directory,
        ),
        ollama=OllamaSettings(
            base_url=environment.ollama_base_url,
            embedding_model=environment.ollama_embedding_model,
            chat_model=environment.ollama_chat_model,
            timeout_seconds=environment.ollama_timeout_seconds,
        ),
        chroma=ChromaSettings(
            persist_directory=environment.chroma_persist_directory,
            collection_name=environment.chroma_collection_name,
        ),
        indexing=IndexingSettings(
            chunk_size=environment.indexing_chunk_size,
            chunk_overlap=environment.indexing_chunk_overlap,
        ),
    )


def persist_chat_model(
    model: str,
) -> None:
    """Persist the active chat model in the environment configuration."""

    _ENV_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines: list[str] = []

    if _ENV_FILE.exists():
        lines = _ENV_FILE.read_text(
            encoding="utf-8",
        ).splitlines()

    assignment = f"{_CHAT_MODEL_ENV_KEY}={model}"

    updated = False
    next_lines: list[str] = []

    for line in lines:
        if line.startswith(
            f"{_CHAT_MODEL_ENV_KEY}=",
        ):
            next_lines.append(
                assignment,
            )
            updated = True

        else:
            next_lines.append(
                line,
            )

    if not updated:
        next_lines.append(
            assignment,
        )

    _ENV_FILE.write_text(
        "\n".join(
            next_lines,
        )
        + "\n",
        encoding="utf-8",
    )

    os.environ[
        _CHAT_MODEL_ENV_KEY
    ] = model

    get_settings.cache_clear()
