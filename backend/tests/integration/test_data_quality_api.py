"""Integration tests for Data Quality Summary API."""

from fastapi.testclient import TestClient


def test_data_quality_summary_endpoint(client: TestClient):
    res = client.get("/api/v1/data-quality/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_transactions" in data
    assert "valid_transactions" in data
    assert "warning_transactions" in data
    assert "invalid_transactions" in data
    assert "possible_duplicates" in data
    assert "missing_categories" in data
    assert "future_transactions" in data
    assert "high_value_transactions" in data
    assert "total_income" in data
    assert "total_expenses" in data
