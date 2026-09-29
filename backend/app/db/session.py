"""Database connection, engine configuration, resilient fallback, and session dependency."""

from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from app.core.config import settings
from app.core.logging import logger


def normalize_db_url(url: str) -> str:
    """Normalizes Postgres URL schemes provided by cloud hosts like Render or Railway."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def init_engine() -> Engine:
    """Initializes database engine targeting PostgreSQL with seamless fallback to SQLite if PostgreSQL is unavailable."""
    target_url = normalize_db_url(settings.DATABASE_URL)

    if target_url.startswith("postgresql"):
        try:
            pg_engine = create_engine(
                target_url,
                connect_args={"connect_timeout": 3},
                pool_pre_ping=True,
                echo=False
            )
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected successfully to primary PostgreSQL database at %s", target_url.split("@")[-1])
            return pg_engine
        except Exception as exc:
            logger.warning(
                "Primary PostgreSQL database is not reachable (%s). "
                "Operating with local persistent SQLite fallback at %s for development.",
                exc,
                settings.SQLITE_FALLBACK_URL
            )
            return create_engine(
                settings.SQLITE_FALLBACK_URL,
                connect_args={"check_same_thread": False},
                echo=False
            )
    else:
        connect_args = {"check_same_thread": False} if target_url.startswith("sqlite") else {}
        return create_engine(
            target_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=False
        )


engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health(custom_engine: Optional[Engine] = None) -> bool:
    """Performs a quick SELECT 1 check to verify database health."""
    active_engine = custom_engine or engine
    try:
        with active_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return False
