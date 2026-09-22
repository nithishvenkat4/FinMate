"""FinMate FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    FinMateException,
    finmate_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.core.logging import logger, setup_logging
from app.db.base import Base
from app.db.session import engine, check_db_health
import app.models  # Ensures all ORM models are registered with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Initializing %s v%s in [%s] environment", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)

    # In dev or test environments, ensure tables are present
    if settings.APP_ENV in ("development", "test"):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database schema tables verified/created.")
        except Exception as exc:
            logger.warning("Could not automatically run create_all on startup: %s", exc)

    db_ok = check_db_health()
    logger.info("Initial database connectivity check: %s", "CONNECTED" if db_ok else "UNAVAILABLE")

    yield

    # Shutdown
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="FinMate — Personal Financial Decision Agent Backend API (Phase 0 Foundation)",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [str(settings.CORS_ORIGINS)]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(FinMateException, finmate_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Routers
app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
