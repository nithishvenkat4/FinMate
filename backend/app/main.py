"""FinMate FastAPI Application Entrypoint."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
from app.scripts.seed_demo_data import seed_demo_data
import app.models  # Ensures all ORM models are registered with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Initializing %s v%s in [%s] environment", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)

    # In dev, test, or production environments, ensure tables and demo data are present
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema tables verified/created.")
        seed_demo_data()
        logger.info("Demo dataset verified/seeded.")
    except Exception as exc:
        logger.warning("Could not automatically initialize/seed database on startup: %s", exc)

    db_ok = check_db_health()
    logger.info("Initial database connectivity check: %s", "CONNECTED" if db_ok else "UNAVAILABLE")

    yield

    # Shutdown
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="FinMate — Personal Financial Decision Agent Backend API",
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

# Frontend Single Page Application (SPA) Serving
possible_dist_paths = [
    os.getenv("FRONTEND_DIST_PATH", ""),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend_dist")),
    os.path.abspath("/app/frontend_dist"),
]
frontend_dist = next((p for p in possible_dist_paths if p and os.path.exists(p) and os.path.isdir(p)), None)

if frontend_dist:
    logger.info("Frontend static build detected at: %s", frontend_dist)
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str = ""):
        # Serve exact file if it exists in dist (e.g. favicon.svg, icons.svg)
        target_file = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        # Otherwise fallback to index.html for client-side routing
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend build index.html not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

