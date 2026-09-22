"""Investments API endpoints."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.exceptions import EntityNotFoundException
from app.db.session import get_db
from app.models.investment import Investment
from app.repositories.investment_repo import InvestmentRepository
from app.repositories.user_repo import UserRepository
from app.schemas.common import MessageResponse
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentResponse,
    InvestmentUpdate,
)

router = APIRouter(prefix="/investments", tags=["Investments"])


def resolve_user_id(user_id: Optional[uuid.UUID], db: Session) -> uuid.UUID:
    if user_id:
        return user_id
    user_repo = UserRepository(db)
    return user_repo.get_or_create_default_user().id


@router.get("", response_model=List[InvestmentResponse])
def get_investments(
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Lists all user investment holdings."""
    uid = resolve_user_id(user_id, db)
    repo = InvestmentRepository(db)
    return repo.get_all_by_user(uid)


@router.post("", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
def create_investment(
    inv_in: InvestmentCreate,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Records a new investment holding."""
    uid = inv_in.user_id or resolve_user_id(user_id, db)
    repo = InvestmentRepository(db)
    inv = Investment(
        user_id=uid,
        asset_name=inv_in.asset_name.strip(),
        investment_type=inv_in.investment_type.strip(),
        quantity=inv_in.quantity,
        current_value=inv_in.current_value
    )
    return repo.create(inv)


@router.get("/{investment_id}", response_model=InvestmentResponse)
def get_investment(
    investment_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Retrieves an investment by ID."""
    uid = resolve_user_id(user_id, db)
    repo = InvestmentRepository(db)
    inv = repo.get_by_id_and_user(investment_id, uid)
    if not inv:
        raise EntityNotFoundException("Investment", investment_id)
    return inv


@router.put("/{investment_id}", response_model=InvestmentResponse)
def update_investment(
    investment_id: uuid.UUID,
    inv_in: InvestmentUpdate,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Updates an investment holding."""
    uid = resolve_user_id(user_id, db)
    repo = InvestmentRepository(db)
    inv = repo.get_by_id_and_user(investment_id, uid)
    if not inv:
        raise EntityNotFoundException("Investment", investment_id)

    if inv_in.asset_name is not None:
        inv.asset_name = inv_in.asset_name.strip()
    if inv_in.investment_type is not None:
        inv.investment_type = inv_in.investment_type.strip()
    if inv_in.quantity is not None:
        inv.quantity = inv_in.quantity
    if inv_in.current_value is not None:
        inv.current_value = inv_in.current_value

    return repo.update(inv)


@router.delete("/{investment_id}", response_model=MessageResponse)
def delete_investment(
    investment_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Deletes an investment record."""
    uid = resolve_user_id(user_id, db)
    repo = InvestmentRepository(db)
    inv = repo.get_by_id_and_user(investment_id, uid)
    if not inv:
        raise EntityNotFoundException("Investment", investment_id)
    repo.delete(inv)
    return MessageResponse(message="Investment successfully deleted")
