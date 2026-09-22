"""Data Quality Metrics API endpoint."""

import datetime
from decimal import Decimal
from typing import Optional
import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.transaction import Transaction
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])


class DataQualitySummaryResponse(BaseModel):
    total_transactions: int = Field(default=0, description="Total transactions in the database")
    valid_transactions: int = Field(default=0, description="Transactions passing all quality checks with zero warnings")
    warning_transactions: int = Field(default=0, description="Transactions flagged with review warnings")
    invalid_transactions: int = Field(default=0, description="Rejected transactions (rejected at ingestion, 0 in DB)")
    possible_duplicates: int = Field(default=0, description="Transactions flagged as potential duplicates")
    missing_categories: int = Field(default=0, description="Transactions assigned to generic fallback categories")
    future_transactions: int = Field(default=0, description="Transactions dated in the future")
    high_value_transactions: int = Field(default=0, description="Transactions exceeding high-value threshold (₹10L)")
    total_income: Decimal = Decimal("0.00")
    total_expenses: Decimal = Decimal("0.00")


def resolve_user_id(user_id: Optional[uuid.UUID], db: Session) -> uuid.UUID:
    if user_id:
        return user_id
    user_repo = UserRepository(db)
    return user_repo.get_or_create_default_user().id


@router.get("/summary", response_model=DataQualitySummaryResponse)
def get_data_quality_summary(
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Calculates data quality metrics and audit health statistics."""
    uid = resolve_user_id(user_id, db)
    today = datetime.date.today()

    transactions = db.query(Transaction).filter(Transaction.user_id == uid).all()
    total_count = len(transactions)

    valid_count = 0
    warning_count = 0
    duplicate_count = 0
    missing_cat_count = 0
    future_count = 0
    high_val_count = 0
    total_inc = Decimal("0.00")
    total_exp = Decimal("0.00")

    for tx in transactions:
        has_warnings = False
        if tx.data_quality_flags:
            flags = str(tx.data_quality_flags)
            if "POSSIBLE_DUPLICATE" in flags:
                duplicate_count += 1
                has_warnings = True
            if "FUTURE_TRANSACTION_DATE" in flags:
                future_count += 1
                has_warnings = True
            if "LARGE_TRANSACTION_AMOUNT" in flags:
                high_val_count += 1
                has_warnings = True
            if "CATEGORY" in flags:
                missing_cat_count += 1
                has_warnings = True

        if tx.transaction_date > today and not has_warnings:
            future_count += 1
            has_warnings = True

        if tx.amount >= Decimal("1000000.00") and not has_warnings:
            high_val_count += 1
            has_warnings = True

        if tx.category in ("Other", "Uncategorized"):
            missing_cat_count += 1

        if has_warnings or tx.data_quality_flags:
            warning_count += 1
        else:
            valid_count += 1

        if tx.transaction_type == "income":
            total_inc += tx.amount
        elif tx.transaction_type == "expense":
            total_exp += tx.amount

    return DataQualitySummaryResponse(
        total_transactions=total_count,
        valid_transactions=valid_count,
        warning_transactions=warning_count,
        invalid_transactions=0,
        possible_duplicates=duplicate_count,
        missing_categories=missing_cat_count,
        future_transactions=future_count,
        high_value_transactions=high_val_count,
        total_income=total_inc,
        total_expenses=total_exp
    )
