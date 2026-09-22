"""Data Engineering & Quality domain models, severity classifications, and result schemas."""

import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class Severity(str, Enum):
    ERROR = "error"      # Row cannot safely enter clean dataset
    WARNING = "warning"  # Row may be valid but should be reviewed
    INFO = "info"        # Informational note / auto-normalization applied


class QualityIssue(BaseModel):
    severity: Severity
    rule_code: str
    message: str
    field: Optional[str] = None


class RawTransactionRow(BaseModel):
    row_number: int
    raw_date: Optional[str] = None
    raw_description: Optional[str] = None
    raw_amount: Optional[str] = None
    raw_type: Optional[str] = None
    raw_category: Optional[str] = None
    raw_notes: Optional[str] = None
    extra_fields: Dict[str, Any] = Field(default_factory=dict)


class NormalizedTransactionRow(BaseModel):
    transaction_date: datetime.date
    description: str
    amount: Decimal
    transaction_type: str  # 'income' or 'expense'
    category: str
    notes: Optional[str] = None


class RowValidationResult(BaseModel):
    row_number: int
    raw_data: Dict[str, Any]
    normalized_data: Optional[NormalizedTransactionRow] = None
    is_valid: bool
    is_duplicate_candidate: bool = False
    issues: List[QualityIssue] = Field(default_factory=list)


class ImportSummaryResult(BaseModel):
    import_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    filename: str
    source_type: str = "csv_import"
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    warning_rows: int = 0
    duplicate_rows: int = 0
    status: str = "completed"  # 'completed', 'completed_with_warnings', 'failed'
    errors: List[str] = Field(default_factory=list)
    row_results: List[RowValidationResult] = Field(default_factory=list)
