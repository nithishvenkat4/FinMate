"""User management API endpoints."""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.exceptions import EntityNotFoundException, DuplicateEntityException
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user(db: Session = Depends(get_db)):
    """Retrieves the default demo user session for Phase 0."""
    repo = UserRepository(db)
    return repo.get_or_create_default_user()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Creates a new user record."""
    repo = UserRepository(db)
    existing = repo.get_by_email(user_in.email)
    if existing:
        raise DuplicateEntityException("User", "email", user_in.email)

    user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip()
    )
    return repo.create(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieves a user by ID."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise EntityNotFoundException("User", user_id)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: uuid.UUID, user_in: UserUpdate, db: Session = Depends(get_db)):
    """Updates user name or email."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise EntityNotFoundException("User", user_id)

    if user_in.name is not None:
        user.name = user_in.name.strip()
    if user_in.email is not None:
        existing = repo.get_by_email(user_in.email)
        if existing and existing.id != user.id:
            raise DuplicateEntityException("User", "email", user_in.email)
        user.email = user_in.email.lower().strip()

    return repo.update(user)
