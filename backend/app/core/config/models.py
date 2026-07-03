"""Typed configuration model definitions."""

from pathlib import Path

from pydantic import BaseModel, Field


class ServerSettings(BaseModel):
    """HTTP server configuration."""

    host: str = "127.0.0.1"
    port: int = 8000


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    json_logs: bool = False


class StorageSettings(BaseModel):
    """Filesystem storage configuration."""

    root_directory: Path = Path(".local_openclaw")


class OllamaSettings(BaseModel):
    """Ollama client configuration."""

    base_url: str = "http://localhost:11434"

    embedding_model: str = "nomic-embed-text"

    chat_model: str = "qwen3.6"

    timeout_seconds: int = 120


class ChromaSettings(BaseModel):
    """ChromaDB configuration."""

    persist_directory: Path = Path(
        ".local_openclaw/index/chroma",
    )

    collection_name: str = "repository_chunks"


class IndexingSettings(BaseModel):
    """Repository indexing configuration."""

    chunk_size: int = 512
    chunk_overlap: int = 64


class ApplicationSettings(BaseModel):
    """Application configuration root."""

    server: ServerSettings = Field(
        default_factory=ServerSettings,
    )

    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
    )

    storage: StorageSettings = Field(
        default_factory=StorageSettings,
    )

    ollama: OllamaSettings = Field(
        default_factory=OllamaSettings,
    )

    chroma: ChromaSettings = Field(
        default_factory=ChromaSettings,
    )

    indexing: IndexingSettings = Field(
        default_factory=IndexingSettings,
    )