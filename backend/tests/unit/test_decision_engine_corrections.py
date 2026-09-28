"""Unit Tests for Phase 5 Correction & Polish:
- Decision-type-aware scenario generation (purchase, saving, expense_change, goal_contribution, debt_payment, investment, subscription, income_change, custom)
- User-controllable and actual discretionary-spending calculations
- Savings coverage terminology and calculation
- Transparent goal timeline methodology
- Edge cases: zero savings, zero income, completed goals, insufficient data
"""

import datetime
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.goal import Goal
from app.models.profile import FinancialProfile
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.decision import DecisionSimulateRequest
from app.services.decision_engine import FinancialDecisionEngine


@pytest.fixture
def correction_test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = User(id=uuid.uuid4(), name="Correction Pass User", email="correct@finmate.test")
    session.add(user)

    profile = FinancialProfile(
        user_id=user.id,
        monthly_income=Decimal("60000.00"),
        monthly_fixed_expenses=Decimal("42000.00"),
        current_savings=Decimal("120000.00"),
        risk_preference="moderate"
    )
    session.add(profile)

    # Add a discretionary dining expense transaction to verify actual discretionary calculation
    txn = Transaction(
        user_id=user.id,
        transaction_type="expense",
        category="Dining",
        amount=Decimal("8000.00"),
        description="Restaurants and dining",
        transaction_date=datetime.date.today(),
    )
    session.add(txn)

    # Goal: Higher Education Target ₹3,00,000, current ₹1,20,000
    today = datetime.date.today()
    goal = Goal(
        user_id=user.id,
        name="Higher Education",
        target_amount=Decimal("300000.00"),
        current_amount=Decimal("120000.00"),
        target_date=datetime.date(today.year + 1, today.month, 1),
        priority="high"
    )
    session.add(goal)
    session.commit()

    yield session, user.id, goal.id
    session.close()


def test_baseline_actual_discretionary_and_savings_coverage(correction_test_db):
    session, user_id, _ = correction_test_db
    engine = FinancialDecisionEngine(session)

    baseline = engine.get_base_financial_state(user_id)

    # Monthly income 60,000, expenses 42,000, surplus 18,000
    assert baseline.monthly_income == Decimal("60000.00")
    assert baseline.monthly_expenses == Decimal("42000.00")
    assert baseline.monthly_surplus == Decimal("18000.00")
    # Discretionary spending derived from dining transaction: ₹8,000
    assert baseline.monthly_discretionary_spending == Decimal("8000.00")
    # Savings coverage: 120,000 / 42,000 = 2.9 months
    assert baseline.savings_coverage_months == Decimal("2.9")
    assert baseline.emergency_buffer_months == Decimal("2.9")
    # Note contains transparent terminology
    assert any("Savings coverage is based on your current savings" in note for note in baseline.notes)


def test_purchase_user_controllable_discretionary_reduction(correction_test_db):
    session, user_id, goal_id = correction_test_db
    engine = FinancialDecisionEngine(session)

    # User explicitly sets discretionary reduction of ₹2,000 in custom_parameters
    req = DecisionSimulateRequest(
        decision_type="purchase",
        amount=Decimal("20000.00"),
        title="Laptop Purchase",
        category="Education",
        affected_goal_id=goal_id,
        custom_parameters={"discretionary_reduction_amount": 2000}
    )

    res = engine.simulate_decision(user_id=user_id, request=req)
    assert len(res.scenarios) == 3

    s3 = res.scenarios[2]
    assert "Trim Discretionary" in s3.name
    # Expense reduced by ₹2,000 (from 42,000 to 40,000)
    assert s3.financial_impact.new_monthly_expenses == Decimal("40000.00")
    assert s3.financial_impact.expense_change == Decimal("-2000.00")
    # Monthly surplus increased by ₹2,000 (from 18,000 to 20,000)
    assert s3.financial_impact.new_monthly_surplus == Decimal("20000.00")
    assert s3.financial_impact.surplus_change == Decimal("2000.00")
    # Assumption states the user assumption transparently
    assert any("₹2,000.00/month" in a for a in s3.assumptions)


def test_savings_decision_type_aware_ladder(correction_test_db):
    session, user_id, _ = correction_test_db
    engine = FinancialDecisionEngine(session)

    req = DecisionSimulateRequest(
        decision_type="saving",
        amount=Decimal("5000.00"),
        title="Save ₹5,000 more every month",
    )

    res = engine.simulate_decision(user_id=user_id, request=req)
    assert len(res.scenarios) == 3

    # Option A: Current Plan
    assert res.scenarios[0].name == "Current Savings Plan"
    # Option B: Save ₹5,000 more
    assert "+₹5,000.00/mo" in res.scenarios[1].name
    assert res.scenarios[1].financial_impact.surplus_change == Decimal("5000.00")
    # Option C: Save ₹10,000 more (Stretch Target)
    assert "+₹10,000.00/mo" in res.scenarios[2].name
    assert res.scenarios[2].financial_impact.surplus_change == Decimal("10000.00")
    # No "wait 2 months" scenario
    assert not any("Wait" in s.name for s in res.scenarios)


def test_expense_change_scenarios(correction_test_db):
    session, user_id, _ = correction_test_db
    engine = FinancialDecisionEngine(session)

    req = DecisionSimulateRequest(
        decision_type="expense_change",
        amount=Decimal("5000.00"),
        title="Rent Increase",
    )

    res = engine.simulate_decision(user_id=user_id, request=req)
    assert len(res.scenarios) == 3

    # Option A: Absorb
    assert res.scenarios[0].name == "Absorb Expense Increase"
    assert res.scenarios[0].financial_impact.surplus_change == Decimal("-5000.00")
    # Option B: Counterbalance with cuts
    assert res.scenarios[1].name == "Counterbalance with Budget Cuts"
    assert res.scenarios[1].financial_impact.surplus_change == Decimal("0.00")
    # Option C: Income target offset
    assert "Increase Monthly Income Target" in res.scenarios[2].name


def test_goal_contribution_scenarios(correction_test_db):
    session, user_id, goal_id = correction_test_db
    engine = FinancialDecisionEngine(session)

    req = DecisionSimulateRequest(
        decision_type="goal_contribution",
        amount=Decimal("20000.00"),
        title="Contribute ₹20,000 to Education Goal",
        affected_goal_id=goal_id
    )

    res = engine.simulate_decision(user_id=user_id, request=req)
    assert len(res.scenarios) == 3

    # Option A: Lump Sum Now
    assert res.scenarios[0].name == "Lump Sum Contribution Now"
    assert res.scenarios[0].financial_impact.cash_position_change == Decimal("-20000.00")
    # Option B: Spread Across 3 Months
    assert res.scenarios[1].name == "Spread Across 3 Months"
    # Option C: Maintain Current Pace
    assert res.scenarios[2].name == "Maintain Current Contribution Pace"
    assert res.scenarios[2].financial_impact.cash_position_change == Decimal("0.00")


def test_debt_payment_scenarios(correction_test_db):
    session, user_id, _ = correction_test_db
    engine = FinancialDecisionEngine(session)

    req = DecisionSimulateRequest(
        decision_type="debt_payment",
        amount=Decimal("30000.00"),
        title="Credit Card Balance Repayment",
    )

    res = engine.simulate_decision(user_id=user_id, request=req)
    assert len(res.scenarios) == 3

    assert res.scenarios[0].name == "Clear Debt Now"
    assert res.scenarios[0].financial_impact.savings_change == Decimal("-30000.00")
    assert "Pay Partially" in res.scenarios[1].name
    assert res.scenarios[2].name == "Maintain Current Scheduled Repayment"


def test_investment_scenarios_informational_only(correction_test_db):
    session, user_id, _ = correction_test_db
    engine = FinancialDecisionEngine(session)

    req = DecisionSimulateRequest(
        decision_type="investment",
        amount=Decimal("25000.00"),
        title="Index Fund Allocation",
    )

    res = engine.simulate_decision(user_id=user_id, request=req)
    assert len(res.scenarios) == 3

    # Informational only: verifies 0 capital appreciation assumptions
    s2 = res.scenarios[1]
    assert any("0% guaranteed capital appreciation" in a for a in s2.assumptions)
    assert s2.financial_impact.cash_position_change == Decimal("-25000.00")


def test_subscription_scenarios(correction_test_db):
    session, user_id, _ = correction_test_db
    engine = FinancialDecisionEngine(session)

    req = DecisionSimulateRequest(
        decision_type="subscription",
        amount=Decimal("1000.00"),
        title="Streaming Subscription",
    )

    res = engine.simulate_decision(user_id=user_id, request=req)
    assert len(res.scenarios) == 3

    # Option A: Add subscription
    assert res.scenarios[0].name == "Add Subscription"
    assert res.scenarios[0].financial_impact.surplus_change == Decimal("-1000.00")
    # Option B: Do not add
    assert res.scenarios[1].name == "Do Not Add Subscription"
    assert res.scenarios[1].financial_impact.surplus_change == Decimal("0.00")
    # Option C: Offset
    assert "Offset Subscription" in res.scenarios[2].name


def test_income_change_scenarios(correction_test_db):
    session, user_id, _ = correction_test_db
    engine = FinancialDecisionEngine(session)

    req = DecisionSimulateRequest(
        decision_type="income_change",
        amount=Decimal("5000.00"),
        title="Salary Increment",
    )

    res = engine.simulate_decision(user_id=user_id, request=req)
    assert len(res.scenarios) == 3

    assert "Expand Monthly Surplus" in res.scenarios[0].name
    assert res.scenarios[0].financial_impact.surplus_change == Decimal("5000.00")
    assert "Direct Additional Income to Savings Reserve" in res.scenarios[1].name
    assert "Direct Additional Income to Goals" in res.scenarios[2].name


def test_edge_case_completed_goal(correction_test_db):
    session, user_id, _ = correction_test_db
    # Create already completed goal (current >= target)
    completed_goal = Goal(
        user_id=user_id,
        name="Emergency Pad",
        target_amount=Decimal("50000.00"),
        current_amount=Decimal("50000.00"),
        target_date=datetime.date.today() + datetime.timedelta(days=180),
        priority="low"
    )
    session.add(completed_goal)
    session.commit()

    engine = FinancialDecisionEngine(session)
    req = DecisionSimulateRequest(
        decision_type="purchase",
        amount=Decimal("10000.00"),
        title="Minor Purchase",
        affected_goal_id=completed_goal.id
    )

    res = engine.simulate_decision(user_id=user_id, request=req)
    assert len(res.scenarios) > 0
    # Goal impact should indicate completed or 0 months remaining
    comp_impact = [g for s in res.scenarios for g in s.goal_impact if g.goal_id == completed_goal.id]
    assert len(comp_impact) > 0
    assert comp_impact[0].remaining_amount == Decimal("0.00")
    assert comp_impact[0].estimated_months_to_goal == 0


def test_edge_case_zero_income_and_zero_savings():
    engine_mock = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine_mock)
    Session = sessionmaker(bind=engine_mock)
    session = Session()

    u = User(id=uuid.uuid4(), name="Zero User", email="zero_edge@test.com")
    session.add(u)
    p = FinancialProfile(
        user_id=u.id,
        monthly_income=Decimal("0.00"),
        monthly_fixed_expenses=Decimal("0.00"),
        current_savings=Decimal("0.00")
    )
    session.add(p)
    session.commit()

    dec_engine = FinancialDecisionEngine(session)
    req = DecisionSimulateRequest(
        decision_type="purchase",
        amount=Decimal("5000.00"),
        title="Laptop",
    )
    res = dec_engine.simulate_decision(user_id=u.id, request=req)

    assert res.baseline.has_sufficient_data is False
    assert res.baseline.savings_coverage_months is None
    assert any("exceeds total recorded savings" in w.lower() for w in res.warnings)
    session.close()
