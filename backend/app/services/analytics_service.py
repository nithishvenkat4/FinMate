"""Analytics service computing deterministic financial metrics."""

from decimal import Decimal
import uuid
from sqlalchemy.orm import Session
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.profile_repo import ProfileRepository
from app.repositories.goal_repo import GoalRepository
from app.repositories.investment_repo import InvestmentRepository
from app.schemas.analytics import AnalyticsSummaryResponse, CategorySpendingItem
from app.services.calculations import (
    calculate_savings,
    calculate_savings_rate,
    calculate_percentage,
)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.tx_repo = TransactionRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.goal_repo = GoalRepository(db)
        self.investment_repo = InvestmentRepository(db)

    def get_summary(self, user_id: uuid.UUID) -> AnalyticsSummaryResponse:
        # 1. Fetch transaction totals
        totals = self.tx_repo.get_totals_by_type(user_id)
        total_income = totals.get("income", Decimal("0.00"))
        total_expenses = totals.get("expense", Decimal("0.00"))

        # 2. Deterministic calculations
        net_savings = calculate_savings(total_income, total_expenses)
        savings_rate = calculate_savings_rate(total_income, net_savings)
        tx_count = self.tx_repo.count_by_user(user_id)

        # 3. Profile details
        profile = self.profile_repo.get_by_user_id(user_id)
        profile_income = profile.monthly_income if profile else Decimal("0.00")
        profile_fixed_exp = profile.monthly_fixed_expenses if profile else Decimal("0.00")
        profile_savings = profile.current_savings if profile else Decimal("0.00")

        # 4. Goals and Investments counts/totals
        goals_count = self.goal_repo.count_by_user(user_id)
        investments_total = self.investment_repo.get_total_value(user_id)

        # 5. Category breakdown
        raw_breakdown = self.tx_repo.get_category_breakdown(user_id, transaction_type="expense")
        category_items = []
        for cat, cat_tot, count in raw_breakdown:
            pct = calculate_percentage(cat_tot, total_expenses)
            category_items.append(
                CategorySpendingItem(
                    category=cat,
                    total_amount=cat_tot,
                    percentage=pct,
                    transaction_count=count
                )
            )

        return AnalyticsSummaryResponse(
            total_income=total_income,
            total_expenses=total_expenses,
            net_savings=net_savings,
            savings_rate=savings_rate,
            transaction_count=tx_count,
            profile_monthly_income=profile_income,
            profile_monthly_fixed_expenses=profile_fixed_exp,
            profile_current_savings=profile_savings,
            active_goals_count=goals_count,
            total_investments_value=investments_total,
            category_breakdown=category_items,
            recent_cash_flow=[]
        )
