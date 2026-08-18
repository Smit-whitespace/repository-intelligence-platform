"""Typed configuration model definitions."""

from pydantic import BaseModel, Field


class ServerSettings(BaseModel):
    """HTTP server configuration."""

    host: str = "127.0.0.1"
    port: int = 8000


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    json_logs: bool = False


class OllamaSettings(BaseModel):
    """Ollama client configuration."""

    base_url: str = "http://localhost:11434"

    embedding_model: str = "nomic-embed-text"

    chat_model: str = "qwen3:8b"

    timeout_seconds: int = 120


class ChromaSettings(BaseModel):
    """ChromaDB configuration.

    The persist directory is intentionally not configurable here: it is
    derived from the opened project root (``<root>/.local_openclaw/index/chroma``)
    so that storage identity never depends on the process working directory.
    """

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

    ollama: OllamaSettings = Field(
        default_factory=OllamaSettings,
    )

    chroma: ChromaSettings = Field(
        default_factory=ChromaSettings,
    )

    indexing: IndexingSettings = Field(
        default_factory=IndexingSettings,
    )