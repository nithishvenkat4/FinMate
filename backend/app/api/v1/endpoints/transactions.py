"""Transactions API endpoints."""

import datetime
import math
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.transaction import (
    SmsTransactionCreate,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def resolve_user_id(user_id: Optional[uuid.UUID], db: Session) -> uuid.UUID:
    if user_id:
        return user_id
    user_repo = UserRepository(db)
    return user_repo.get_or_create_default_user().id


@router.get("", response_model=PaginatedResponse[TransactionResponse])
def get_transactions(
    transaction_type: Optional[str] = Query(None, description="'income' or 'expense'"),
    category: Optional[str] = Query(None, description="Category filter"),
    start_date: Optional[datetime.date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[datetime.date] = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Lists transactions with filtering and pagination."""
    uid = resolve_user_id(user_id, db)
    service = TransactionService(db)
    skip = (page - 1) * page_size

    items, total = service.list(
        user_id=uid,
        transaction_type=transaction_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=page_size
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=[TransactionResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_in: TransactionCreate,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Creates a new transaction record."""
    uid = tx_in.user_id or resolve_user_id(user_id, db)
    service = TransactionService(db)
    created = service.create(uid, tx_in)
    return TransactionResponse.model_validate(created)


@router.post("/from-sms", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction_from_sms(
    tx_in: SmsTransactionCreate,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Ingests a structured transaction extracted from an SMS message with duplicate protection."""
    uid = resolve_user_id(user_id, db)
    service = TransactionService(db)
    created = service.create_from_sms(uid, tx_in)
    return TransactionResponse.model_validate(created)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Retrieves a single transaction by ID."""
    uid = resolve_user_id(user_id, db)
    service = TransactionService(db)
    tx = service.get_by_id(transaction_id, uid)
    return TransactionResponse.model_validate(tx)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: uuid.UUID,
    tx_in: TransactionUpdate,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Updates an existing transaction."""
    uid = resolve_user_id(user_id, db)
    service = TransactionService(db)
    updated = service.update(transaction_id, uid, tx_in)
    return TransactionResponse.model_validate(updated)


@router.delete("/{transaction_id}", response_model=MessageResponse)
def delete_transaction(
    transaction_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Deletes a transaction record."""
    uid = resolve_user_id(user_id, db)
    service = TransactionService(db)
    service.delete(transaction_id, uid)
    return MessageResponse(message="Transaction successfully deleted")
