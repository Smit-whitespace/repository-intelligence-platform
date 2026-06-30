"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def get_health() -> dict[str, str]:
    """Return application health status."""

    return {
        "status": "healthy",
        "application": "local-openclaw",
        "version": "0.1.0",
    }