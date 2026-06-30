"""Application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api import api_router
from app.core.logging.factory import get_logger

from app.api.exception_handlers import (
    register_exception_handlers,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(
    application: FastAPI,
) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""

    logger.info(
        "application_started",
    )

    yield

    logger.info(
        "application_stopped",
    )


def create_application() -> FastAPI:
    """Create the FastAPI application."""

    application = FastAPI(
        title="Local OpenClaw",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.include_router(
        api_router,
    )

    register_exception_handlers(
        application,
    )

    return application


app = create_application()