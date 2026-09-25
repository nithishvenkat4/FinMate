"""Transaction request and response schemas."""

import datetime
import uuid
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

TransactionType = Literal["income", "expense"]


class TransactionBase(BaseModel):
    transaction_date: datetime.date = Field(default_factory=datetime.date.today)
    description: str = Field(..., min_length=1, max_length=255, description="Transaction memo/payee")
    amount: Decimal = Field(..., gt=0, description="Transaction amount, strictly positive")
    transaction_type: TransactionType = Field(..., description="'income' or 'expense'")
    category: str = Field(..., min_length=1, max_length=50, description="Spending or income category")


class TransactionCreate(TransactionBase):
    user_id: Optional[uuid.UUID] = None


class TransactionUpdate(BaseModel):
    transaction_date: Optional[datetime.date] = None
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(None, gt=0)
    transaction_type: Optional[TransactionType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)


class TransactionResponse(TransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    notes: Optional[str] = None
    source_type: Optional[str] = None
    source_reference: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class SmsTransactionCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Transaction amount, strictly positive")
    transaction_date: datetime.date = Field(default_factory=datetime.date.today)
    type: TransactionType = Field(default="expense", description="'income' or 'expense'")
    category: str = Field(default="Other", min_length=1, max_length=50)
    description: str = Field(default="SMS Transaction", min_length=1, max_length=255)
    source: str = Field(default="sms", description="Source identifier")
    sender: str = Field(..., min_length=1, max_length=100, description="Financial institution sender ID")
    sms_hash: str = Field(..., min_length=6, max_length=255, description="Deterministic SMS hash for deduplication")

    model_config = ConfigDict(populate_by_name=True)
