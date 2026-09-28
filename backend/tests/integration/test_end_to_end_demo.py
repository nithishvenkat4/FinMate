"""End-to-End Demo Test for Phase 5 Correction Pass.

Simulates the exact user scenario:
Income: ₹60,000
Expenses: ₹42,000
Savings: ₹1,20,000
Education Goal: Target ₹3,00,000, Current ₹1,20,000
Decision: "Can I buy a ₹20,000 laptop?"

Verifies:
1. Natural language parameter extraction
2. Deterministic baseline calculations
3. Multi-scenario generation (Buy Now, Wait, Trim Discretionary)
4. "What changes?" quantitative diff
5. Transparent goal impact estimation
6. Side-by-side scenario comparison
7. Objective trade-off explanation without guarantees
"""

import datetime
from decimal import Decimal
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.goal import Goal
from app.models.profile import FinancialProfile
from app.models.user import User
from app.services.decision_engine import FinancialDecisionEngine
from app.ai.orchestrator.orchestrator import AIOrchestrator


def test_end_to_end_laptop_demo(client: TestClient, db_session: Session):
    db = db_session
    # 1. Set up user state
    user = User(id=uuid.uuid4(), name="Priya Demo", email="priya.demo@finmate.test")
    db.add(user)

    profile = FinancialProfile(
        user_id=user.id,
        monthly_income=Decimal("60000.00"),
        monthly_fixed_expenses=Decimal("42000.00"),
        current_savings=Decimal("120000.00"),
        risk_preference="moderate",
    )
    db.add(profile)

    today = datetime.date.today()
    goal = Goal(
        user_id=user.id,
        name="Higher Education",
        target_amount=Decimal("300000.00"),
        current_amount=Decimal("120000.00"),
        target_date=datetime.date(today.year + 1, today.month, min(today.day, 28)),
        priority="high",
    )
    db.add(goal)
    db.commit()

    # 2. Natural language extraction via orchestrator
    orchestrator = AIOrchestrator(db)
    query = "Can I buy a ₹20,000 laptop?"
    extracted = orchestrator.extract_decision_parameters(query)

    assert extracted is not None
    assert extracted["decision_type"] == "purchase"
    assert extracted["amount"] == Decimal("20000.00")
    assert "Laptop" in extracted["title"]

    # 3. Deterministic calculation via FinancialDecisionEngine
    engine = FinancialDecisionEngine(db)
    baseline = engine.get_base_financial_state(user.id)

    assert baseline.monthly_income == Decimal("60000.00")
    assert baseline.monthly_expenses == Decimal("42000.00")
    assert baseline.monthly_surplus == Decimal("18000.00")
    assert baseline.current_savings == Decimal("120000.00")
    # Savings coverage = 120,000 / 42,000 = 2.9 months
    assert baseline.savings_coverage_months == Decimal("2.9")

    # 4. Run API simulation
    sim_payload = {
        "decision_type": extracted["decision_type"],
        "amount": str(extracted["amount"]),
        "title": extracted["title"],
        "category": extracted["category"],
        "affected_goal_id": str(goal.id),
        "save_to_history": True,
    }

    res = client.post(f"/api/v1/decisions/simulate?user_id={user.id}", json=sim_payload)
    assert res.status_code == 200
    sim_data = res.json()

    # 5. Verify "What changes?" and scenarios
    scenarios = sim_data["scenarios"]
    assert len(scenarios) == 3

    # Option A: Buy Now
    buy_now = scenarios[0]
    assert buy_now["name"] == "Buy Now"
    assert Decimal(str(buy_now["financial_impact"]["new_savings"])) == Decimal("100000.00")
    assert Decimal(str(buy_now["financial_impact"]["savings_change"])) == Decimal("-20000.00")
    assert Decimal(str(buy_now["financial_impact"]["new_monthly_surplus"])) == Decimal("18000.00")
    assert Decimal(str(buy_now["financial_impact"]["surplus_change"])) == Decimal("0.00")
    # Coverage: 100,000 / 42,000 = 2.4 months
    assert Decimal(str(buy_now["financial_impact"]["savings_coverage_months"])) == Decimal("2.4")

    # Option B: Wait & Save
    wait_sc = scenarios[1]
    assert "Wait" in wait_sc["name"]
    # Baseline liquid savings protected
    assert Decimal(str(wait_sc["financial_impact"]["new_savings"])) >= Decimal("120000.00")

    # Option C: Buy Now + Trim Discretionary
    trim_sc = scenarios[2]
    assert "Trim Discretionary" in trim_sc["name"]
    assert Decimal(str(trim_sc["financial_impact"]["new_monthly_surplus"])) > Decimal("18000.00")

    # Verify Goal Impact
    goal_impacts = buy_now["goal_impact"]
    assert len(goal_impacts) > 0
    assert goal_impacts[0]["goal_name"] == "Higher Education"
    assert goal_impacts[0]["timeline_difference_months"] is not None

    # Verify Explanation What Changes / What Stays Unchanged
    explanation = sim_data["explanation"]
    assert any("₹120,000.00 → ₹100,000.00" in change for change in explanation["what_changes"])
    assert any("Monthly income" in stay for stay in explanation["what_stays_unchanged"])
    assert any("Monthly surplus" in stay for stay in explanation["what_stays_unchanged"])

    # 6. Verify side-by-side comparison endpoint
    comp_res = client.post("/api/v1/decisions/compare", json={"simulation": sim_data})
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    matrix = {row["metric"]: row for row in comp_data["comparison_matrix"]}
    assert "Savings Coverage" in matrix
    assert matrix["Savings Coverage"]["baseline"] == "2.9 mo"
    assert "2.4 mo" in matrix["Savings Coverage"]["scenarios"]["Buy Now"]

    # 7. Verify History listing
    list_res = client.get(f"/api/v1/decisions?user_id={user.id}")
    assert list_res.status_code == 200
    history_items = list_res.json()["items"]
    assert len(history_items) >= 1
    assert history_items[0]["title"] == "Laptop Purchase (₹20,000)"
    assert history_items[0]["goal_impact_summary"] is not None
