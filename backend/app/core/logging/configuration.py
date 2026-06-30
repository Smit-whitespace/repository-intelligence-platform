"""Logging configuration utilities."""

import logging

import structlog


def configure_logging(
    level: str,
    json_logs: bool,
) -> None:
    """Configure structured application logging."""

    renderer: structlog.typing.Processor

    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    logging.basicConfig(
        level=getattr(
            logging,
            level.upper(),
            logging.INFO,
        ),
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(
                fmt="iso",
            ),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )