"""Integration tests for Financial Profile API."""

from fastapi.testclient import TestClient


def test_profile_get_and_update(client: TestClient):
    # 1. Get profile (auto initializes default if absent)
    res = client.get("/api/v1/profile")
    assert res.status_code == 200
    profile = res.json()
    assert "monthly_income" in profile
    assert "current_savings" in profile

    # 2. Update profile
    update_payload = {
        "monthly_income": "75000.00",
        "monthly_fixed_expenses": "28000.00",
        "current_savings": "180000.00",
        "risk_preference": "aggressive"
    }
    res = client.put("/api/v1/profile", json=update_payload)
    assert res.status_code == 200
    updated = res.json()
    assert updated["monthly_income"] == "75000.00"
    assert updated["risk_preference"] == "aggressive"
