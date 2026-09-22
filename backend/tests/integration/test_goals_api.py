"""Integration tests for Goals API."""

from fastapi.testclient import TestClient


def test_goal_crud_and_progress(client: TestClient):
    # 1. Create a goal
    goal_payload = {
        "name": "Emergency Fund",
        "target_amount": "100000.00",
        "current_amount": "40000.00",
        "target_date": "2026-12-31",
        "priority": "high"
    }
    res = client.post("/api/v1/goals", json=goal_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Emergency Fund"
    # Progress: 40000 / 100000 = 40%
    assert data["progress_percentage"] == "40.00"
    goal_id = data["id"]

    # 2. List goals
    res = client.get("/api/v1/goals")
    assert res.status_code == 200
    assert any(g["id"] == goal_id for g in res.json())

    # 3. Update current amount
    res = client.put(f"/api/v1/goals/{goal_id}", json={"current_amount": "75000.00"})
    assert res.status_code == 200
    updated = res.json()
    assert updated["current_amount"] == "75000.00"
    assert updated["progress_percentage"] == "75.00"

    # 4. Delete goal
    res = client.delete(f"/api/v1/goals/{goal_id}")
    assert res.status_code == 200

    # 5. Verify 404
    res = client.get(f"/api/v1/goals/{goal_id}")
    assert res.status_code == 404
