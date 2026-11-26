"""Application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api import api_router
from app.core.logging.factory import get_logger
from app.core.config.settings import settings
from app.core.security.api_token import (
    SIGN_IN_CODE_TTL_SECONDS,
    api_token_path,
    sign_in_url,
)
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
        "name": "Workspace",
        "description": (
            "Read-only repository tools for external clients: read files, "
            "list the tree, text search, symbol lookup, semantic search."
        ),
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

    # The link carries a single-use code, never the API token, so this
    # output and any log file kept from it reveal nothing once the link
    # has been used or has expired.
    logger.info(
        "sign_in",
        open_this_link=sign_in_url(),
        link_works=f"once, for {SIGN_IN_CODE_TTL_SECONDS // 60} minutes",
        token_file=str(
            api_token_path(),
        ),
    )

    yield

    logger.info(
        "application_stopped",
    )


def allowed_browser_origins() -> list[str]:
    """Origins whose pages may call the API directly from a browser.

    The default dev server, plus wherever ``LOC_SERVER_FRONTEND_URL`` says
    the app runs, so the sign-in link never opens an app the API refuses.
    (With the dev server's ``/api`` proxy, requests are same-origin and
    this list is not consulted.)
    """

    configured = urlsplit(
        settings.server.frontend_url,
    )

    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    if configured.scheme and configured.netloc:
        origin = f"{configured.scheme}://{configured.netloc}"

        if origin not in origins:
            origins.append(
                origin,
            )

    return origins


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
        TrustedHostMiddleware,
        allowed_hosts=settings.server.allowed_hosts,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_browser_origins(),
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
