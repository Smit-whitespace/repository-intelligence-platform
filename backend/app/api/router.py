"""Application API router configuration."""

from fastapi import APIRouter

from app.api.routes.chat import (
    router as chat_router,
)
from app.api.routes.editing import (
    router as editing_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.models import (
    router as models_router,
)
from app.api.routes.projects import (
    router as projects_router,
)
from app.api.routes.repository import (
    router as repository_router,
)
from app.api.routes.system import (
    router as system_router,
)

api_router = APIRouter(
    prefix="/api/v1",
)

api_router.include_router(
    health_router,
)

api_router.include_router(
    projects_router,
)

api_router.include_router(
    repository_router,
)

api_router.include_router(
    models_router,
)

api_router.include_router(
    system_router,
)

api_router.include_router(
    chat_router,
)

api_router.include_router(
    editing_router,
)
