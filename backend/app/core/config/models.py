"""Typed configuration model definitions."""

from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator


class ServerSettings(BaseModel):
    """HTTP server configuration."""

    host: str = "127.0.0.1"
    port: int = 8000

    allowed_hosts: list[str] = Field(
        default_factory=lambda: [
            "localhost",
            "127.0.0.1",
        ],
    )
    """Host header values the API accepts.

    Rejecting other Host headers blocks DNS rebinding: a web page on an
    attacker's domain that re-resolves to 127.0.0.1 would otherwise be
    able to call this API as same-origin.
    """

    frontend_url: str = "http://localhost:5173"
    """Where the RIP app runs; used for the sign-in link printed at startup."""

    @field_validator(
        "frontend_url",
    )
    @classmethod
    def _require_http_url(
        cls,
        value: str,
    ) -> str:
        # Refused at startup instead of silently dropped: without a scheme
        # the sign-in link is not clickable, and the origin cannot be
        # allowed for browser requests.
        url = urlsplit(
            value,
        )

        try:
            # .port raises for a non-numeric or out-of-range port.
            valid = (
                url.scheme.lower() in {"http", "https"}
                and bool(url.hostname)
                and (url.port is None or url.port > 0)
            )

        except ValueError:
            valid = False

        if not valid:
            raise ValueError(
                "LOC_SERVER_FRONTEND_URL must start with http:// or https:// "
                "and name a host with an optional port from 1 to 65535, for "
                f"example http://localhost:5173 (got {value!r}).",
            )

        return value


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


class ModelsSettings(BaseModel):
    """Where the model configuration file lives."""

    config_path: str = ""
    """Empty means the per-user default, ~/.local_openclaw/models.json."""


class SecuritySettings(BaseModel):
    """Where RIP's per-user secrets live."""

    integrity_key_path: str = ""
    """Empty means the per-user default, ~/.local_openclaw/integrity.key."""

    api_token_path: str = ""
    """Empty means the per-user default, ~/.local_openclaw/api.token."""


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

    models: ModelsSettings = Field(
        default_factory=ModelsSettings,
    )

    security: SecuritySettings = Field(
        default_factory=SecuritySettings,
    )

    chroma: ChromaSettings = Field(
        default_factory=ChromaSettings,
    )

    indexing: IndexingSettings = Field(
        default_factory=IndexingSettings,
    )