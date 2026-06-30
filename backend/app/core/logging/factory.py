"""Logger factory functions."""

import structlog


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structured logger."""

    return structlog.get_logger(name)