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
