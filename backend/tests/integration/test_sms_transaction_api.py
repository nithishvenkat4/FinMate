"""Integration tests for SMS transaction ingestion API."""

from fastapi.testclient import TestClient


def test_create_sms_transaction_success(client: TestClient):
    payload = {
        "amount": "850.00",
        "transaction_date": "2026-09-25",
        "type": "expense",
        "category": "Other",
        "description": "SMS Transaction",
        "source": "sms",
        "sender": "HDFCBK",
        "sms_hash": "a1b2c3d4e5f67890abcdef1234567890"
    }
    res = client.post("/api/v1/transactions/from-sms", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["amount"] == "850.00"
    assert data["transaction_type"] == "expense"
    assert data["category"] == "Other"
    assert data["description"] == "SMS Transaction"
    assert data["source_type"] == "sms"
    assert data["source_reference"] == "a1b2c3d4e5f67890abcdef1234567890"
    assert "Sender: HDFCBK" in (data.get("notes") or "")

    # Verify transaction appears in the normal transactions ledger list
    res_list = client.get("/api/v1/transactions")
    assert res_list.status_code == 200
    list_data = res_list.json()
    matches = [t for t in list_data["items"] if t["id"] == data["id"]]
    assert len(matches) == 1
    assert matches[0]["amount"] == "850.00"


def test_duplicate_sms_transaction_rejected(client: TestClient):
    sms_hash = "unique_hash_9876543210_hdfc"
    payload = {
        "amount": "1200.00",
        "transaction_date": "2026-09-25",
        "type": "expense",
        "category": "Other",
        "description": "SMS Transaction",
        "source": "sms",
        "sender": "SBIINB",
        "sms_hash": sms_hash
    }
    # First submission -> 201 Created
    res1 = client.post("/api/v1/transactions/from-sms", json=payload)
    assert res1.status_code == 201

    # Second submission with the exact same sms_hash -> 409 Conflict
    res2 = client.post("/api/v1/transactions/from-sms", json=payload)
    assert res2.status_code == 409
    err = res2.json()
    assert "error" in err
    assert err["error"]["code"] == "DUPLICATE_TRANSACTION"


def test_create_sms_credit_transaction(client: TestClient):
    payload = {
        "amount": "15000.00",
        "transaction_date": "2026-09-25",
        "type": "income",
        "category": "Other",
        "description": "SMS Transaction",
        "source": "sms",
        "sender": "ICICIB",
        "sms_hash": "income_hash_999888777"
    }
    res = client.post("/api/v1/transactions/from-sms", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["amount"] == "15000.00"
    assert data["transaction_type"] == "income"


def test_invalid_sms_transaction_payloads(client: TestClient):
    # 1. Amount <= 0
    res_neg = client.post("/api/v1/transactions/from-sms", json={
        "amount": "-50.00",
        "transaction_date": "2026-09-25",
        "type": "expense",
        "sender": "AXISBK",
        "sms_hash": "neg_amount_hash_1"
    })
    assert res_neg.status_code == 422

    # 2. Missing sender
    res_no_sender = client.post("/api/v1/transactions/from-sms", json={
        "amount": "100.00",
        "transaction_date": "2026-09-25",
        "type": "expense",
        "sms_hash": "no_sender_hash_1"
    })
    assert res_no_sender.status_code == 422

    # 3. Missing sms_hash
    res_no_hash = client.post("/api/v1/transactions/from-sms", json={
        "amount": "100.00",
        "transaction_date": "2026-09-25",
        "type": "expense",
        "sender": "AXISBK"
    })
    assert res_no_hash.status_code == 422
