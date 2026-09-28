"""Integration tests for Decisions & What-If Simulation API (Phase 5)."""

from fastapi.testclient import TestClient


def test_simulate_decision_and_validation(client: TestClient):
    # 1. Validation error on amount <= 0
    invalid_payload = {
        "decision_type": "purchase",
        "amount": "-500.00",
        "title": "Invalid Purchase",
    }
    res = client.post("/api/v1/decisions/simulate", json=invalid_payload)
    assert res.status_code == 422

    # 2. Valid purchase simulation
    valid_payload = {
        "decision_type": "purchase",
        "amount": "20000.00",
        "title": "Buy a laptop",
        "category": "Education",
        "save_to_history": False,
    }
    res = client.post("/api/v1/decisions/simulate", json=valid_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["decision"]["title"] == "Buy a laptop"
    assert data["decision"]["amount"] == "20000.00"
    assert "baseline" in data
    assert len(data["scenarios"]) >= 2
    # Verify exact decimal currency representations
    assert data["scenarios"][0]["name"] == "Buy Now"
    assert data["scenarios"][0]["financial_impact"]["cash_position_change"] == "-20000.00"
    assert "explanation" in data
    assert len(data["assumptions"]) >= 2


def test_decision_history_lifecycle(client: TestClient):
    # 1. Simulate and save to history
    payload = {
        "decision_type": "purchase",
        "amount": "25000.00",
        "title": "Smartphone Upgrade",
        "category": "Electronics",
        "save_to_history": True,
    }
    res = client.post("/api/v1/decisions/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    decision_id = data["decision_id"]
    assert decision_id is not None

    # 2. List saved decisions in history
    res = client.get("/api/v1/decisions")
    assert res.status_code == 200
    list_data = res.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == decision_id for d in list_data["items"])

    # 3. Retrieve specific saved decision details
    res = client.get(f"/api/v1/decisions/{decision_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["title"] == "Smartphone Upgrade"
    assert len(detail["scenarios"]) >= 2

    # 4. Delete saved decision
    res = client.delete(f"/api/v1/decisions/{decision_id}")
    assert res.status_code == 200

    # 5. Verify 404
    res = client.get(f"/api/v1/decisions/{decision_id}")
    assert res.status_code == 404


def test_scenario_comparison_matrix(client: TestClient):
    # Run simulation first
    sim_payload = {
        "decision_type": "purchase",
        "amount": "15000.00",
        "title": "Office Desk",
        "category": "Furniture",
    }
    sim_res = client.post("/api/v1/decisions/simulate", json=sim_payload)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()

    # Request comparison matrix
    compare_res = client.post("/api/v1/decisions/compare", json={"simulation": sim_data})
    assert compare_res.status_code == 200
    compare_data = compare_res.json()

    assert "comparison_matrix" in compare_data
    assert len(compare_data["comparison_matrix"]) >= 4
    metrics = [row["metric"] for row in compare_data["comparison_matrix"]]
    assert "Immediate Cash Outlay" in metrics
    assert "Remaining Liquid Savings" in metrics
    assert "Monthly Surplus" in metrics


def test_ai_advisor_natural_language_decision_task(client: TestClient):
    # Submit natural language decision question
    task_payload = {
        "query": "Can I afford a ₹20,000 laptop next month without hurting my education goal?"
    }
    res = client.post("/api/v1/agent/tasks", json=task_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in ["completed", "waiting_for_user"]
    assert "AIOrchestrator" in data["agents_used"]
    assert len(data["tradeoffs"]) >= 2
    assert "INR 20,000 laptop" in data["summary"]
