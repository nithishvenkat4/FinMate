"""Unit tests for CSV Parser."""

import pytest
from app.data.parser import CSVParser, CSVParseException


def test_parse_valid_standard_csv():
    content = """date,description,amount,type,category,notes
2026-09-01,Salary,60000,income,Salary,Monthly salary
2026-09-02,Swiggy,450,expense,Food,Dinner
"""
    rows, errors = CSVParser.parse(content)
    assert len(rows) == 2
    assert rows[0].raw_date == "2026-09-01"
    assert rows[0].raw_description == "Salary"
    assert rows[0].raw_amount == "60000"
    assert rows[0].raw_type == "income"
    assert rows[0].raw_category == "Salary"
    assert rows[0].raw_notes == "Monthly salary"


def test_parse_semicolon_delimited_csv():
    content = """date;description;amount;type;category
2026-09-04;Uber;300;expense;Transport
"""
    rows, errors = CSVParser.parse(content)
    assert len(rows) == 1
    assert rows[0].raw_description == "Uber"
    assert rows[0].raw_amount == "300"


def test_parse_missing_required_column():
    content = """date,description,category
2026-09-01,Salary,Salary
"""
    with pytest.raises(CSVParseException) as exc_info:
        CSVParser.parse(content)
    assert "Missing required CSV columns" in str(exc_info.value)
    assert "amount" in exc_info.value.missing_columns


def test_parse_extra_columns_tolerated():
    content = """date,description,amount,type,extra_col1,extra_col2
2026-09-01,Bonus,5000,income,foo,bar
"""
    rows, errors = CSVParser.parse(content)
    assert len(rows) == 1
    assert rows[0].extra_fields.get("extra_col1") == "foo"
    assert rows[0].extra_fields.get("extra_col2") == "bar"


def test_parse_empty_content_raises():
    with pytest.raises(CSVParseException):
        CSVParser.parse("   \n\n  ")


def test_parse_bank_statement_format():
    # Comma-separated bank statement format
    content = """Txn Date,Description,Cheque No,Debit Amount,Credit Amount,Balance
2026-09-01,Monthly Salary,REF9876,,65000.00,125000.00
2026-09-02,Swiggy Takeout,CHQ1234,450.00,,124550.00
2026-09-03,Atm Withdrawal,-,2000.00,,122550.00
"""
    rows, errors = CSVParser.parse(content)
    assert len(rows) == 3

    # Row 1: Credit (Income)
    assert rows[0].raw_date == "2026-09-01"
    assert rows[0].raw_description == "Monthly Salary"
    assert rows[0].raw_amount == "65000.00"
    assert rows[0].raw_type == "income"
    assert "REF9876" in rows[0].raw_notes
    assert rows[0].extra_fields.get("balance") == "125000.00"

    # Row 2: Debit (Expense)
    assert rows[1].raw_date == "2026-09-02"
    assert rows[1].raw_description == "Swiggy Takeout"
    assert rows[1].raw_amount == "450.00"
    assert rows[1].raw_type == "expense"
    assert "CHQ1234" in rows[1].raw_notes
    assert rows[1].extra_fields.get("balance") == "124550.00"

    # Row 3: Debit with empty/hyphen cheque no
    assert rows[2].raw_amount == "2000.00"
    assert rows[2].raw_type == "expense"


def test_parse_tab_delimited_bank_statement():
    # Tab-separated netbanking export
    content = "Txn Date\tDescription\tCheque No\tDebit Amount\tCredit Amount\tBalance\n2026-09-05\tAmazon India\t\t1299.00\t\t121251.00\n2026-09-06\tConsulting Dividend\tCHQ554\t\t15000.00\t136251.00\n"
    rows, errors = CSVParser.parse(content)
    assert len(rows) == 2
    assert rows[0].raw_description == "Amazon India"
    assert rows[0].raw_amount == "1299.00"
    assert rows[0].raw_type == "expense"
    assert rows[1].raw_description == "Consulting Dividend"
    assert rows[1].raw_amount == "15000.00"
    assert rows[1].raw_type == "income"
    assert "CHQ554" in rows[1].raw_notes

