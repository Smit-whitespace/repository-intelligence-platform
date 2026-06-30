"""Application settings access."""

from app.core.config.provider import get_settings

settings = get_settings()

__all__ = (
    "get_settings",
    "settings",
)