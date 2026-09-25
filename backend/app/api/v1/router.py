"""API v1 master router module."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    users,
    profile,
    categories,
    transactions,
    goals,
    investments,
    analytics,
    imports,
    data_quality,
    ai,
    agent,
)

api_router = APIRouter()

api_router.include_router(users.router)
api_router.include_router(profile.router)
api_router.include_router(categories.router)
api_router.include_router(transactions.router)
api_router.include_router(goals.router)
api_router.include_router(investments.router)
api_router.include_router(analytics.router)
api_router.include_router(imports.router)
api_router.include_router(data_quality.router)
api_router.include_router(ai.router)
api_router.include_router(agent.router)

