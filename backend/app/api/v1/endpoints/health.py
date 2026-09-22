"""Health check endpoint."""

from fastapi import APIRouter
from app.core.config import settings
from app.db.session import check_db_health

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    """System health check endpoint.

    Returns:
        JSON response with service status and database connectivity.
    """
    db_ok = check_db_health()
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": "finmate-backend",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": "connected" if db_ok else "disconnected"
    }
