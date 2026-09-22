"""Custom domain exceptions and centralized error handling."""

from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging import logger


class FinMateException(Exception):
    """Base exception for FinMate domain errors."""
    def __init__(self, message: str, code: str = "FINMATE_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class EntityNotFoundException(FinMateException):
    """Exception raised when an entity is not found."""
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' was not found.",
            code=f"{entity_name.upper()}_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )


class DuplicateEntityException(FinMateException):
    """Exception raised when attempting to create a duplicate unique entity."""
    def __init__(self, entity_name: str, field: str, value: Any):
        super().__init__(
            message=f"{entity_name} with {field} '{value}' already exists.",
            code=f"DUPLICATE_{entity_name.upper()}",
            status_code=status.HTTP_409_CONFLICT
        )


class FinancialCalculationException(FinMateException):
    """Exception raised for invalid financial calculation inputs."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="INVALID_CALCULATION_INPUT",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


async def finmate_exception_handler(request: Request, exc: FinMateException) -> JSONResponse:
    """Handles domain-specific FinMate exceptions."""
    logger.warning("FinMateException on %s: %s (Code: %s)", request.url.path, exc.message, exc.code)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic request validation exceptions."""
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    formatted_errors = [
        {
            "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg"),
            "type": err.get("type")
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed. Please check the supplied fields.",
                "details": formatted_errors
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches all unhandled exceptions without leaking stack traces or credentials."""
    logger.error("Unhandled server exception on %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": None
            }
        }
    )
