"""Application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.logging.factory import get_logger
from app.core.config.settings import settings
from app.core.logging.configuration import (
    configure_logging,
)

from app.api.exception_handlers import (
    register_exception_handlers,
)

logger = get_logger(__name__)

OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Backend liveness and version endpoints.",
    },
    {
        "name": "Projects",
        "description": "RIP project metadata and workspace registration endpoints.",
    },
    {
        "name": "Repository",
        "description": "Repository scanning, indexing, and summary endpoints.",
    },
    {
        "name": "Chat",
        "description": "Repository-aware chat endpoints.",
    },
    {
        "name": "Editing",
        "description": "Planning, apply, snapshot, and rollback endpoints.",
    },
    {
        "name": "Models",
        "description": "Model discovery and active model management endpoints.",
    },
    {
        "name": "System",
        "description": "RIP status, capability, and version discovery endpoints.",
    },
]


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

    configure_logging(
        level=settings.logging.level,
        json_logs=settings.logging.json_logs,
    )

    application = FastAPI(
        title="Repository Intelligence Platform (RIP)",
        version="0.1.0",
        description=(
            "Repository Intelligence Platform (RIP) backend API for "
            "repository-aware coding assistance."
        ),
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(
        api_router,
    )

    register_exception_handlers(
        application,
    )

    return application


app = create_application()
