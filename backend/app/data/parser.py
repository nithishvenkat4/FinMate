"""Robust CSV Parser for financial transaction ingestion."""

import csv
import io
import re
from typing import List, Tuple
from app.data.models import RawTransactionRow


class CSVParseException(Exception):
    def __init__(self, message: str, missing_columns: List[str] = None):
        super().__init__(message)
        self.message = message
        self.missing_columns = missing_columns or []


class CSVParser:
    COLUMN_ALIASES = {
        "date": ["date", "transaction_date", "txn_date", "date_time", "posting_date", "value_date"],
        "description": ["description", "memo", "payee", "details", "narrative", "narration", "particulars", "transaction_details"],
        "amount": ["amount", "txn_amount", "value", "sum", "transaction_amount"],
        "type": ["type", "transaction_type", "txn_type", "credit_debit", "cr_dr"],
        "category": ["category", "cat", "tag"],
        "notes": ["notes", "note", "comment", "remarks", "reference", "ref_no", "reference_no"],
        "cheque_no": ["cheque_no", "cheque_number", "chq_no", "chq_ref_no", "chq", "cheque", "check_no", "ref_cheque_no"],
        "debit": ["debit", "debit_amount", "dr", "dr_amount", "withdrawal", "withdrawal_amount", "debit_inr"],
        "credit": ["credit", "credit_amount", "cr", "cr_amount", "deposit", "deposit_amount", "credit_inr"],
        "balance": ["balance", "closing_balance", "account_balance", "running_balance", "bal", "available_balance"],
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
        sample = text[:4096]
        first_line = sample.splitlines()[0] if sample.splitlines() else sample
        tabs = first_line.count("\t")
        commas = first_line.count(",")
        semis = first_line.count(";")
        if tabs > commas and tabs > semis:
            return "\t"
        if semis > commas and semis > tabs:
            return ";"
        return ","

    @classmethod
    def map_header(cls, header: str) -> str:
        clean = header.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "")
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
        has_date = "date" in mapped_headers
        has_desc = "description" in mapped_headers
        has_amount = "amount" in mapped_headers
        has_type = "type" in mapped_headers
        has_debit_credit = "debit" in mapped_headers or "credit" in mapped_headers

        if not (has_date and has_desc and (has_amount or has_debit_credit)):
            missing = []
            if not has_date:
                missing.append("date")
            if not has_desc:
                missing.append("description")
            if not has_amount and not has_debit_credit:
                missing.append("amount")
            if not has_type and not has_debit_credit and not has_amount:
                missing.append("type")
            raise CSVParseException(
                f"Missing required CSV columns: {', '.join(sorted(missing))}. "
                f"Required: date, description, and either amount/type or Debit/Credit columns.",
                missing_columns=list(missing)
            )

        rows: List[RawTransactionRow] = []
        errors: List[str] = []

        def _clean_num(s: str) -> float:
            clean = re.sub(r"[^\d.-]", "", s.strip())
            try:
                return float(clean) if clean else 0.0
            except ValueError:
                return 0.0

        for row_idx, row in enumerate(reader, start=2):
            if not row or all(not cell.strip() for cell in row):
                continue  # Skip blank row

            row_dict = {}
            extra_dict = {}
            for col_idx, cell in enumerate(row):
                if col_idx < len(mapped_headers):
                    col_name = mapped_headers[col_idx]
                    val = cell.strip()
                    if col_name in cls.COLUMN_ALIASES:
                        row_dict[col_name] = val
                    else:
                        extra_dict[col_name] = val

            # Dual-column Debit / Credit transformation
            if has_debit_credit and not row_dict.get("amount"):
                debit_str = row_dict.get("debit", "")
                credit_str = row_dict.get("credit", "")
                debit_val = _clean_num(debit_str)
                credit_val = _clean_num(credit_str)

                if debit_val > 0:
                    row_dict["amount"] = re.sub(r"[^\d.-]", "", debit_str)
                    row_dict["type"] = "expense"
                elif credit_val > 0:
                    row_dict["amount"] = re.sub(r"[^\d.-]", "", credit_str)
                    row_dict["type"] = "income"
                elif debit_str and not credit_str:
                    row_dict["amount"] = re.sub(r"[^\d.-]", "", debit_str) or "0.00"
                    row_dict["type"] = "expense"
                elif credit_str and not debit_str:
                    row_dict["amount"] = re.sub(r"[^\d.-]", "", credit_str) or "0.00"
                    row_dict["type"] = "income"

            # Retain Cheque No in notes and extra_fields
            chq_val = row_dict.get("cheque_no") or extra_dict.get("cheque_no")
            if chq_val and chq_val.strip() and chq_val.strip() not in ("-", "—", "N/A"):
                chq_note = f"Cheque No: {chq_val.strip()}"
                curr_note = row_dict.get("notes") or ""
                row_dict["notes"] = f"{curr_note} | {chq_note}".strip(" |") if curr_note else chq_note
                extra_dict["cheque_no"] = chq_val.strip()

            # Retain Balance in extra_fields
            bal_val = row_dict.get("balance") or extra_dict.get("balance")
            if bal_val and bal_val.strip():
                extra_dict["balance"] = bal_val.strip()

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
