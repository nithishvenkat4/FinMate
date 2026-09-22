"""Transaction Category repository."""

from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.category import TransactionCategory
from app.repositories.base import BaseRepository


DEFAULT_CATEGORIES = [
    ("Salary", "income", "Primary employment compensation"),
    ("Freelance", "income", "Contract and consulting earnings"),
    ("Investment", "income", "Dividends, interest, and capital gains"),
    ("Other Income", "income", "Miscellaneous incoming funds"),
    ("Food", "expense", "Groceries, dining out, and food delivery"),
    ("Shopping", "expense", "Retail, clothing, electronics, and personal goods"),
    ("Transport", "expense", "Public transit, fuel, cabs, and vehicle maintenance"),
    ("Utilities", "expense", "Electricity, water, gas, and internet"),
    ("Rent", "expense", "Housing rent and maintenance fees"),
    ("Healthcare", "expense", "Medical, pharmacy, doctor visits, and insurance"),
    ("Education", "expense", "Tuition, courses, books, and educational material"),
    ("Entertainment", "expense", "Subscriptions, movies, games, and recreation"),
    ("Other", "expense", "General uncategorized expenses"),
]


class CategoryRepository(BaseRepository[TransactionCategory]):
    def __init__(self, db: Session):
        super().__init__(TransactionCategory, db)

    def get_by_name(self, name: str) -> Optional[TransactionCategory]:
        clean = name.strip().title()
        stmt = select(TransactionCategory).where(TransactionCategory.name == clean)
        return self.db.scalars(stmt).first()

    def get_all_active(self) -> List[TransactionCategory]:
        stmt = select(TransactionCategory).where(TransactionCategory.is_active == True).order_by(TransactionCategory.name.asc())
        return list(self.db.scalars(stmt).all())

    def get_or_create(self, name: str, category_type: str = "expense") -> TransactionCategory:
        clean = name.strip().title()
        cat = self.get_by_name(clean)
        if not cat:
            cat = TransactionCategory(
                name=clean,
                category_type=category_type.lower() if category_type in ("income", "expense") else "expense",
                description=f"Auto-provisioned category: {clean}",
                is_active=True
            )
            cat = self.create(cat)
        return cat

    def seed_defaults(self) -> None:
        """Provisions standard FinMate categories if they do not exist."""
        for name, c_type, desc in DEFAULT_CATEGORIES:
            existing = self.get_by_name(name)
            if not existing:
                cat = TransactionCategory(
                    name=name,
                    category_type=c_type,
                    description=desc,
                    is_active=True
                )
                self.db.add(cat)
        self.db.commit()
