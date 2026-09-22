"""Deterministic Synthetic Demo Data Generator for FinMate.

Seeds reproducible, synthetic financial records for testing and development.
Command: python -m app.scripts.seed_demo_data
"""

import datetime
from decimal import Decimal
import sys
import uuid

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.category import TransactionCategory
from app.models.goal import Goal
from app.models.investment import Investment
from app.models.profile import FinancialProfile
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.category_repo import CategoryRepository


def seed_demo_data():
    print("=" * 60)
    print("Seeding FinMate Demo Financial Dataset...")
    print("=" * 60)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Categories
        cat_repo = CategoryRepository(db)
        cat_repo.seed_defaults()
        print("[+] Categories verified/seeded.")

        # 2. Get or Create Demo User
        user = db.query(User).filter(User.email == "demo@finmate.local").first()
        if not user:
            user = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                name="Demo User",
                email="demo@finmate.local"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[+] Created Demo User: {user.name} ({user.email})")
        else:
            print(f"[+] Found existing Demo User: {user.name} ({user.email})")

        # 3. Create or Update Financial Profile
        # Income: ₹60,000 | Fixed: ₹15,000 | Savings: ₹1,20,000 | Risk: Moderate
        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
        if not profile:
            profile = FinancialProfile(
                user_id=user.id,
                monthly_income=Decimal("60000.00"),
                monthly_fixed_expenses=Decimal("15000.00"),
                current_savings=Decimal("120000.00"),
                risk_preference="moderate"
            )
            db.add(profile)
            print("[+] Created Financial Profile: Income=INR 60,000, Fixed=INR 15,000, Savings=INR 1,20,000")
        else:
            profile.monthly_income = Decimal("60000.00")
            profile.monthly_fixed_expenses = Decimal("15000.00")
            profile.current_savings = Decimal("120000.00")
            profile.risk_preference = "moderate"
            print("[+] Updated existing Financial Profile with demo baselines.")

        # 4. Seed Canonical Transactions (Section 20 & 40)
        # Clear existing synthetic demo transactions to maintain idempotency
        db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.source_type.in_(["synthetic", "manual"])
        ).delete(synchronize_session=False)

        demo_transactions = [
            ("Salary", Decimal("60000.00"), "income", "Salary", datetime.date(2026, 9, 1), "Monthly salary deposit"),
            ("Swiggy", Decimal("450.00"), "expense", "Food", datetime.date(2026, 9, 2), "Dinner delivery"),
            ("Amazon", Decimal("1200.00"), "expense", "Shopping", datetime.date(2026, 9, 3), "Electronics accessory"),
            ("Uber", Decimal("300.00"), "expense", "Transport", datetime.date(2026, 9, 4), "Cab ride to office"),
            ("Netflix", Decimal("649.00"), "expense", "Entertainment", datetime.date(2026, 9, 5), "Monthly standard plan"),
            ("Electricity", Decimal("1800.00"), "expense", "Utilities", datetime.date(2026, 9, 6), "Power bill payment"),
        ]

        for desc, amt, t_type, cat_name, t_date, notes in demo_transactions:
            cat = cat_repo.get_or_create(cat_name, t_type)
            tx = Transaction(
                user_id=user.id,
                category_id=cat.id,
                transaction_date=t_date,
                description=desc,
                amount=amt,
                transaction_type=t_type,
                category=cat.name,
                notes=notes,
                source_type="synthetic"
            )
            db.add(tx)
        print(f"[+] Seeded {len(demo_transactions)} canonical demo transactions.")

        # 5. Seed Goals
        # Higher Education (Target: INR 3,00,000, Current: INR 1,20,000)
        # Emergency Fund (Target: INR 2,10,000, Current: INR 1,20,000)
        db.query(Goal).filter(Goal.user_id == user.id).delete(synchronize_session=False)
        goals = [
            Goal(
                user_id=user.id,
                name="Higher Education",
                target_amount=Decimal("300000.00"),
                current_amount=Decimal("120000.00"),
                target_date=datetime.date(2027, 6, 30),
                priority="high"
            ),
            Goal(
                user_id=user.id,
                name="Emergency Fund",
                target_amount=Decimal("210000.00"),
                current_amount=Decimal("120000.00"),
                target_date=datetime.date(2026, 12, 31),
                priority="high"
            ),
        ]
        for g in goals:
            db.add(g)
        print(f"[+] Seeded {len(goals)} demo financial goals.")

        # 6. Seed Investment
        # Tata Silver ETF (Type: ETF, Value: INR 6,000)
        db.query(Investment).filter(Investment.user_id == user.id).delete(synchronize_session=False)
        inv = Investment(
            user_id=user.id,
            asset_name="Tata Silver ETF",
            investment_type="ETF",
            quantity=Decimal("100.0000"),
            current_value=Decimal("6000.00")
        )
        db.add(inv)
        print("[+] Seeded demo investment: Tata Silver ETF (INR 6,000.00).")

        db.commit()
        print("=" * 60)
        print("Demo data seeded successfully and verified!")
        print("=" * 60)

    except Exception as exc:
        db.rollback()
        print(f"[-] Error seeding demo data: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
