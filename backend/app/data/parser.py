"""Robust CSV Parser for financial transaction ingestion."""

import csv
import io
from typing import List, Tuple
from app.data.models import RawTransactionRow


class CSVParseException(Exception):
    def __init__(self, message: str, missing_columns: List[str] = None):
        super().__init__(message)
        self.message = message
        self.missing_columns = missing_columns or []


class CSVParser:
    REQUIRED_COLUMNS = {"date", "description", "amount", "type"}
    COLUMN_ALIASES = {
        "date": ["date", "transaction_date", "txn_date", "date_time"],
        "description": ["description", "memo", "payee", "details", "narrative", "narration"],
        "amount": ["amount", "txn_amount", "value", "sum"],
        "type": ["type", "transaction_type", "txn_type", "credit_debit", "cr_dr"],
        "category": ["category", "cat", "tag"],
        "notes": ["notes", "note", "comment", "remarks"],
    }

    @classmethod
    def decode_content(cls, raw_bytes: bytes) -> str:
        """Decodes bytes trying UTF-8-SIG, UTF-8, then Latin-1."""
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return raw_bytes.decode(enc)
            except UnicodeDecodeError:
                continue
        raise CSVParseException("Unsupported file encoding. Please ensure the CSV is encoded in UTF-8.")

    @classmethod
    def detect_delimiter(cls, text: str) -> str:
        sample = text[:2048]
        if ";" in sample and "," not in sample:
            return ";"
        return ","

    @classmethod
    def map_header(cls, header: str) -> str:
        clean = header.strip().lower().replace(" ", "_").replace("-", "_")
        for canon, aliases in cls.COLUMN_ALIASES.items():
            if clean in aliases:
                return canon
        return clean

    @classmethod
    def parse(cls, content: str) -> Tuple[List[RawTransactionRow], List[str]]:
        """Parses CSV text and returns a list of RawTransactionRow and parsing errors."""
        lines = [line for line in content.splitlines() if line.strip()]
        if not lines:
            raise CSVParseException("The uploaded CSV file is empty.")

        delimiter = cls.detect_delimiter(content)
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)

        try:
            raw_headers = next(reader)
        except StopIteration:
            raise CSVParseException("The CSV file does not contain a header row.")

        mapped_headers = [cls.map_header(h) for h in raw_headers]
        missing = cls.REQUIRED_COLUMNS - set(mapped_headers)
        if missing:
            raise CSVParseException(
                f"Missing required CSV columns: {', '.join(sorted(missing))}. "
                f"Required: date, description, amount, type.",
                missing_columns=list(missing)
            )

        rows: List[RawTransactionRow] = []
        errors: List[str] = []

        for row_idx, row in enumerate(reader, start=2):
            if not row or all(not cell.strip() for cell in row):
                continue  # Skip blank row

            row_dict = {}
            extra_dict = {}
            for col_idx, cell in enumerate(row):
                if col_idx < len(mapped_headers):
                    col_name = mapped_headers[col_idx]
                    if col_name in cls.COLUMN_ALIASES:
                        row_dict[col_name] = cell.strip()
                    else:
                        extra_dict[col_name] = cell.strip()

            raw_row = RawTransactionRow(
                row_number=row_idx,
                raw_date=row_dict.get("date"),
                raw_description=row_dict.get("description"),
                raw_amount=row_dict.get("amount"),
                raw_type=row_dict.get("type"),
                raw_category=row_dict.get("category"),
                raw_notes=row_dict.get("notes"),
                extra_fields=extra_dict
            )
            rows.append(raw_row)

        return rows, errors
