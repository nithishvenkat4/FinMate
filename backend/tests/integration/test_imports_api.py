"""Integration tests for CSV Transaction Import API."""

import io
from fastapi.testclient import TestClient


def test_import_preview_endpoint(client: TestClient):
    csv_data = """date,description,amount,type,category,notes
2026-09-01,Salary,60000,income,Salary,Monthly salary
2026-09-02,Swiggy,450,expense,Food,Dinner
2026-09-03,Invalid Row,not_a_number,expense,Food,Error test
"""
    files = {"file": ("test_import.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/imports/transactions/preview", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 3
    assert data["valid_rows"] == 2
    assert data["invalid_rows"] == 1
    assert data["status"] == "completed_with_warnings"

    # Verify no transactions were persisted in preview mode
    tx_res = client.get("/api/v1/transactions")
    assert not any(t["description"] == "Swiggy" for t in tx_res.json()["items"])


def test_import_persist_endpoint(client: TestClient):
    csv_data = """date,description,amount,type,category,notes
2026-09-01,Salary Credit,60000,income,Salary,Direct deposit
2026-09-02,Electricity Bill,1800,expense,Utilities,September bill
"""
    files = {"file": ("september_txns.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/imports/transactions", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["valid_rows"] == 2
    assert data["invalid_rows"] == 0
    assert data["status"] == "completed"

    # Verify persisted in database with lineage
    tx_res = client.get("/api/v1/transactions")
    items = tx_res.json()["items"]
    salary_tx = next(t for t in items if t["description"] == "Salary Credit")
    assert salary_tx["amount"] == "60000.00"
    assert salary_tx["transaction_type"] == "income"


def test_import_duplicate_warning_detection(client: TestClient):
    # CSV containing two identical rows
    csv_data = """date,description,amount,type,category
2026-09-04,Uber Ride,300,expense,Transport
2026-09-04,Uber Ride,300,expense,Transport
"""
    files = {"file": ("uber_dups.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/imports/transactions", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["duplicate_rows"] >= 1
    assert data["status"] == "completed_with_warnings"


def test_import_invalid_file_type_rejected(client: TestClient):
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
    files = {"file": ("malicious.exe", io.BytesIO(fake_exe), "application/octet-stream")}
    res = client.post("/api/v1/imports/transactions", files=files)
    assert res.status_code == 415
    assert res.json()["error"]["code"] == "INVALID_FILE_TYPE"
