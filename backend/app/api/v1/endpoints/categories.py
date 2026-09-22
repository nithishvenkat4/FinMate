"""Transaction Categories API endpoints."""

import datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from app.core.exceptions import EntityNotFoundException, DuplicateEntityException
from app.db.session import get_db
from app.models.category import TransactionCategory
from app.repositories.category_repo import CategoryRepository

router = APIRouter(prefix="/categories", tags=["Categories"])


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    category_type: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category_type: str = Field(default="expense", pattern="^(income|expense|both)$")
    description: Optional[str] = Field(None, max_length=255)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    category_type: Optional[str] = Field(None, pattern="^(income|expense|both)$")
    description: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("", response_model=List[CategoryResponse])
def get_categories(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Lists available transaction categories."""
    repo = CategoryRepository(db)
    repo.seed_defaults()
    if active_only:
        return repo.get_all_active()
    return repo.get_all()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db)
):
    """Creates a new custom transaction category."""
    repo = CategoryRepository(db)
    clean_name = cat_in.name.strip().title()
    existing = repo.get_by_name(clean_name)
    if existing:
        raise DuplicateEntityException("Category", "name", clean_name)

    cat = TransactionCategory(
        name=clean_name,
        category_type=cat_in.category_type,
        description=cat_in.description.strip() if cat_in.description else None,
        is_active=True
    )
    return repo.create(cat)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    cat_in: CategoryUpdate,
    db: Session = Depends(get_db)
):
    """Updates a category or deactivates it without deleting historical records."""
    repo = CategoryRepository(db)
    cat = repo.get_by_id(category_id)
    if not cat:
        raise EntityNotFoundException("Category", category_id)

    if cat_in.name is not None:
        clean_name = cat_in.name.strip().title()
        existing = repo.get_by_name(clean_name)
        if existing and existing.id != cat.id:
            raise DuplicateEntityException("Category", "name", clean_name)
        cat.name = clean_name

    if cat_in.category_type is not None:
        cat.category_type = cat_in.category_type

    if cat_in.description is not None:
        cat.description = cat_in.description.strip()

    if cat_in.is_active is not None:
        cat.is_active = cat_in.is_active

    return repo.update(cat)
