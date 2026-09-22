"""Application configuration module using Pydantic Settings."""

import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "FinMate"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production-finmate-2026"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database settings
    # Primary default is PostgreSQL; can be overridden via .env
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/finmate_db"

    # Fallback SQLite DB for offline testing/development if needed
    SQLITE_FALLBACK_URL: str = "sqlite:///./finmate.db"

    # CORS settings
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # Logging
    LOG_LEVEL: str = "INFO"

    # Future AI Architecture Placeholders (Phase 1+)
    LLM_PROVIDER: str = ""
    LLM_API_KEY: str = ""
    VECTOR_DATABASE_URL: str = ""
    EMBEDDING_MODEL: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
