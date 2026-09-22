"""CSV Transaction Import API endpoints."""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.core.exceptions import FinMateException
from app.core.logging import logger
from app.data.models import ImportSummaryResult
from app.data.parser import CSVParser, CSVParseException
from app.data.pipeline import IngestionPipeline
from app.db.session import get_db
from app.models.import_record import ImportRecord
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/imports", tags=["Data Ingestion & Imports"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Megabytes


def resolve_user_id(user_id: Optional[uuid.UUID], db: Session) -> uuid.UUID:
    if user_id:
        return user_id
    user_repo = UserRepository(db)
    return user_repo.get_or_create_default_user().id


async def validate_and_read_file(file: UploadFile) -> tuple[str, str]:
    if not file.filename:
        raise FinMateException("No file provided for upload.", code="EMPTY_FILE_NAME")

    if not file.filename.lower().endswith(".csv") and file.content_type not in ("text/csv", "application/vnd.ms-excel", "text/plain"):
        raise FinMateException(
            f"Unsupported file type for '{file.filename}'. Please upload a .csv file.",
            code="INVALID_FILE_TYPE",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_FILE_SIZE:
        raise FinMateException(
            f"File size ({len(raw_bytes) / 1024 / 1024:.2f} MB) exceeds maximum allowed 5 MB.",
            code="FILE_TOO_LARGE",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )

    if not raw_bytes:
        raise FinMateException("The uploaded file is empty.", code="EMPTY_FILE")

    try:
        content = CSVParser.decode_content(raw_bytes)
        return content, file.filename
    except CSVParseException as exc:
        raise FinMateException(exc.message, code="FILE_DECODING_ERROR")


@router.post("/transactions", response_model=ImportSummaryResult)
async def import_transactions_csv(
    file: UploadFile = File(..., description="CSV file containing transactions"),
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Parses, normalizes, validates, and persists transactions from a CSV file."""
    uid = resolve_user_id(user_id, db)
    content, filename = await validate_and_read_file(file)

    result = IngestionPipeline.process_csv(
        user_id=uid,
        content=content,
        filename=filename,
        db=db,
        persist=True
    )
    return result


@router.post("/transactions/preview", response_model=ImportSummaryResult)
async def preview_transactions_csv(
    file: UploadFile = File(..., description="CSV file to preview"),
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Validates and previews a CSV file without persisting transactions."""
    uid = resolve_user_id(user_id, db)
    content, filename = await validate_and_read_file(file)

    result = IngestionPipeline.process_csv(
        user_id=uid,
        content=content,
        filename=filename,
        db=db,
        persist=False
    )
    return result


@router.get("/history")
def get_import_history(
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Returns past CSV batch imports and audit records."""
    uid = resolve_user_id(user_id, db)
    records = db.query(ImportRecord).filter(ImportRecord.user_id == uid).order_by(ImportRecord.created_at.desc()).all()
    return records
