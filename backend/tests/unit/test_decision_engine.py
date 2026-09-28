"""Unit Tests for FinancialDecisionEngine, Decimal Money Calculations, and Scenario Generation (Phase 5)."""

import datetime
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.goal import Goal
from app.models.profile import FinancialProfile
from app.models.user import User
from app.schemas.decision import DecisionSimulateRequest
from app.services.decision_engine import FinancialDecisionEngine


@pytest.fixture
def db_session():
    """In-memory SQLite session with initialized schema for unit testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test user
    user = User(
        id=uuid.uuid4(),
        name="Test Citizen",
        email="citizen@finmate.test"
    )
    session.add(user)

    # Seed profile: Income ₹60,000, Expenses ₹35,000, Savings ₹1,20,000
    profile = FinancialProfile(
        user_id=user.id,
        monthly_income=Decimal("60000.00"),
        monthly_fixed_expenses=Decimal("35000.00"),
        current_savings=Decimal("120000.00"),
        risk_preference="moderate"
    )
    session.add(profile)

    # Seed goal: Education Goal target ₹3,00,000, current ₹1,20,000, target in 12 months
    today = datetime.date.today()
    target_date = datetime.date(today.year + 1, today.month, min(today.day, 28))
    goal = Goal(
        user_id=user.id,
        name="Higher Education",
        target_amount=Decimal("300000.00"),
        current_amount=Decimal("120000.00"),
        target_date=target_date,
        priority="high"
    )
    session.add(goal)
    session.commit()

    yield session, user.id, goal.id
    session.close()


def test_baseline_financial_state_calculation(db_session):
    session, user_id, _ = db_session
    engine = FinancialDecisionEngine(session)

    baseline = engine.get_base_financial_state(user_id)

    assert isinstance(baseline.monthly_income, Decimal)
    assert baseline.monthly_income == Decimal("60000.00")
    assert baseline.monthly_expenses == Decimal("35000.00")
    # Surplus: 60,000 - 35,000 = 25,000.00
    assert baseline.monthly_surplus == Decimal("25000.00")
    assert baseline.current_savings == Decimal("120000.00")
    # Savings rate: (25,000 / 60,000) * 100 = 41.67%
    assert baseline.savings_rate == Decimal("41.67")
    # Emergency buffer: 120,000 / 35,000 = 3.4 months
    assert baseline.emergency_buffer_months == Decimal("3.4")
    assert baseline.has_sufficient_data is True


def test_purchase_simulation_scenarios(db_session):
    session, user_id, goal_id = db_session
    engine = FinancialDecisionEngine(session)

    request = DecisionSimulateRequest(
        decision_type="purchase",
        amount=Decimal("20000.00"),
        title="Laptop Purchase",
        category="Education",
        affected_goal_id=goal_id
    )

    response = engine.simulate_decision(user_id=user_id, request=request)

    assert response.decision["amount"] == Decimal("20000.00")
    assert len(response.scenarios) == 3

    # Scenario 1: Buy Now
    s1 = response.scenarios[0]
    assert s1.name == "Buy Now"
    # Savings should decrease by ₹20,000 (from 120,000 to 100,000)
    assert s1.financial_impact.new_savings == Decimal("100000.00")
    assert s1.financial_impact.savings_change == Decimal("-20000.00")
    # Monthly cashflow surplus remains unchanged at baseline
    assert s1.financial_impact.new_monthly_surplus == Decimal("25000.00")
    assert s1.financial_impact.cash_position_change == Decimal("-20000.00")
    # Goal impact should be computed
    assert len(s1.goal_impact) > 0
    top_goal = s1.goal_impact[0]
    assert top_goal.goal_name == "Higher Education"
    assert top_goal.remaining_amount == Decimal("180000.00")

    # Scenario 2: Wait & Save
    s2 = response.scenarios[1]
    assert "Wait" in s2.name
    # Baseline savings is protected (not reduced below 120,000)
    assert s2.financial_impact.new_savings >= Decimal("120000.00")
    assert s2.financial_impact.cash_position_change == Decimal("0.00")

    # Scenario 3: Buy Now + Discretionary Cut
    s3 = response.scenarios[2]
    assert "Trim Discretionary" in s3.name
    assert s3.financial_impact.new_monthly_surplus > Decimal("25000.00")

    # Transparent Assumptions and Trade-off explanation
    assert len(response.assumptions) >= 3
    assert "Laptop Purchase" in response.explanation.summary
    assert len(response.explanation.what_changes) >= 1
    assert len(response.explanation.what_stays_unchanged) >= 1


def test_savings_boost_simulation(db_session):
    session, user_id, _ = db_session
    engine = FinancialDecisionEngine(session)

    request = DecisionSimulateRequest(
        decision_type="saving",
        amount=Decimal("5000.00"),
        title="Increase Monthly Savings",
        category="Savings"
    )

    response = engine.simulate_decision(user_id=user_id, request=request)
    assert len(response.scenarios) == 3

    # Boosted Scenario
    boosted = response.scenarios[1]
    # Surplus increases by ₹5,000 (from 25,000 to 30,000)
    assert boosted.financial_impact.new_monthly_surplus == Decimal("30000.00")
    assert boosted.financial_impact.surplus_change == Decimal("5000.00")
    # 12-month wealth adds ₹60,000
    assert boosted.financial_impact.savings_change == Decimal("60000.00")


def test_expense_increase_simulation(db_session):
    session, user_id, _ = db_session
    engine = FinancialDecisionEngine(session)

    request = DecisionSimulateRequest(
        decision_type="expense_change",
        amount=Decimal("5000.00"),
        title="Rent Increase",
        category="Rent & Housing"
    )

    response = engine.simulate_decision(user_id=user_id, request=request)
    absorb_sc = response.scenarios[0]

    # Surplus drops by ₹5,000 (from 25,000 to 20,000)
    assert absorb_sc.financial_impact.new_monthly_surplus == Decimal("20000.00")
    assert absorb_sc.financial_impact.surplus_change == Decimal("-5000.00")
    assert absorb_sc.financial_impact.new_monthly_expenses == Decimal("40000.00")


def test_edge_case_amount_exceeds_savings(db_session):
    session, user_id, _ = db_session
    engine = FinancialDecisionEngine(session)

    # User has 120,000 savings; asks to buy something for 150,000
    request = DecisionSimulateRequest(
        decision_type="purchase",
        amount=Decimal("150000.00"),
        title="Luxury Watch",
        category="Shopping"
    )

    response = engine.simulate_decision(user_id=user_id, request=request)

    # Should flag global warning and scenario warning
    assert any("exceeds total recorded savings" in w.lower() for w in response.warnings)
    s1 = response.scenarios[0]
    assert any("exceeds current savings" in w.lower() for w in s1.warnings)
    # Savings cannot drop below zero
    assert s1.financial_impact.new_savings == Decimal("0.00")


def test_edge_case_zero_savings_user():
    engine_mock = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine_mock)
    Session = sessionmaker(bind=engine_mock)
    session = Session()

    u = User(id=uuid.uuid4(), name="Zero Savings", email="zero@test.com")
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
    baseline = dec_engine.get_base_financial_state(u.id)

    assert baseline.monthly_income == Decimal("0.00")
    assert baseline.current_savings == Decimal("0.00")
    assert baseline.has_sufficient_data is False
    assert len(baseline.notes) > 0
    session.close()
