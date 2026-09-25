# ==============================================================================
# Multi-Stage Production Dockerfile for FinMate Unified Web Application
# Stage 1: Build React 19 + Vite Frontend
# Stage 2: Python 3.13 Runtime serving FastAPI API + React Frontend SPA
# ==============================================================================

# Stage 1: Frontend Build
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Unified Backend & Frontend Web Application
FROM python:3.13-slim AS runner

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy backend definition and install dependencies
COPY backend/pyproject.toml backend/README.md ./backend/
WORKDIR /app/backend
RUN uv pip install --system --no-cache -e .

# Copy application source code and migrations
COPY backend/app/ ./app/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini ./

# Copy built frontend SPA assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend_dist

# Set production environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV FRONTEND_DIST_PATH=/app/frontend_dist
ENV PORT=8000

EXPOSE 8000

# Start Uvicorn bound to the dynamic port assigned by cloud host
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
