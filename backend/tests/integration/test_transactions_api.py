"""Integration tests for Transactions API."""

from fastapi.testclient import TestClient


def test_transaction_crud_flow(client: TestClient):
    # 1. Create income transaction
    inc_payload = {
        "description": "Monthly Salary",
        "amount": "60000.00",
        "transaction_type": "income",
        "category": "Salary",
        "transaction_date": "2026-03-01"
    }
    res = client.post("/api/v1/transactions", json=inc_payload)
    assert res.status_code == 201
    inc_data = res.json()
    assert inc_data["description"] == "Monthly Salary"
    assert inc_data["amount"] == "60000.00"
    tx_id = inc_data["id"]

    # 2. Create expense transaction
    exp_payload = {
        "description": "Supermarket Groceries",
        "amount": "4500.00",
        "transaction_type": "expense",
        "category": "Food",
        "transaction_date": "2026-03-05"
    }
    res = client.post("/api/v1/transactions", json=exp_payload)
    assert res.status_code == 201

    # 3. List transactions
    res = client.get("/api/v1/transactions")
    assert res.status_code == 200
    list_data = res.json()
    assert list_data["total"] >= 2
    assert len(list_data["items"]) >= 2

    # 4. Get transaction by ID
    res = client.get(f"/api/v1/transactions/{tx_id}")
    assert res.status_code == 200
    assert res.json()["id"] == tx_id

    # 5. Update transaction
    res = client.put(f"/api/v1/transactions/{tx_id}", json={"description": "Salary Bonus Added", "amount": "65000.00"})
    assert res.status_code == 200
    assert res.json()["description"] == "Salary Bonus Added"
    assert res.json()["amount"] == "65000.00"

    # 6. Delete transaction
    res = client.delete(f"/api/v1/transactions/{tx_id}")
    assert res.status_code == 200

    # 7. Verify deletion
    res = client.get(f"/api/v1/transactions/{tx_id}")
    assert res.status_code == 404
