"""Transaction domain service."""

import datetime
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session
from app.core.exceptions import EntityNotFoundException
from app.core.logging import logger
from app.models.transaction import Transaction
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TransactionRepository(db)

    def create(self, user_id: uuid.UUID, data: TransactionCreate) -> Transaction:
        logger.info("Creating %s transaction for user %s: %s (amount: %s)", data.transaction_type, user_id, data.description, data.amount)
        tx = Transaction(
            user_id=user_id,
            transaction_date=data.transaction_date or datetime.date.today(),
            description=data.description.strip(),
            amount=data.amount,
            transaction_type=data.transaction_type.lower(),
            category=data.category.strip()
        )
        return self.repo.create(tx)

    def get_by_id(self, id: uuid.UUID, user_id: uuid.UUID) -> Transaction:
        tx = self.repo.get_by_id_and_user(id, user_id)
        if not tx:
            raise EntityNotFoundException("Transaction", id)
        return tx

    def list(
        self,
        user_id: uuid.UUID,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Transaction], int]:
        items = self.repo.get_all_by_user(
            user_id=user_id,
            transaction_type=transaction_type,
            category=category,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        total = self.repo.count_by_user(
            user_id=user_id,
            transaction_type=transaction_type,
            category=category,
            start_date=start_date,
            end_date=end_date
        )
        return items, total

    def update(self, id: uuid.UUID, user_id: uuid.UUID, data: TransactionUpdate) -> Transaction:
        tx = self.get_by_id(id, user_id)
        if data.description is not None:
            tx.description = data.description.strip()
        if data.amount is not None:
            tx.amount = data.amount
        if data.transaction_type is not None:
            tx.transaction_type = data.transaction_type.lower()
        if data.category is not None:
            tx.category = data.category.strip()
        if data.transaction_date is not None:
            tx.transaction_date = data.transaction_date

        logger.info("Updated transaction %s for user %s", id, user_id)
        return self.repo.update(tx)

    def delete(self, id: uuid.UUID, user_id: uuid.UUID) -> None:
        tx = self.get_by_id(id, user_id)
        self.repo.delete(tx)
        logger.info("Deleted transaction %s for user %s", id, user_id)
