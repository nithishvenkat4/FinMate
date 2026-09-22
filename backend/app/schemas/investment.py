"""Investment request and response schemas."""

import datetime
import uuid
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class InvestmentBase(BaseModel):
    asset_name: str = Field(..., min_length=1, max_length=150, description="Asset or holding name")
    investment_type: str = Field(..., min_length=1, max_length=50, description="Type: Equity, Mutual Fund, FD, etc.")
    quantity: Decimal = Field(default=Decimal("1.0000"), gt=0, description="Asset units or quantity")
    current_value: Decimal = Field(..., ge=0, description="Current market or estimated value")


class InvestmentCreate(InvestmentBase):
    user_id: Optional[uuid.UUID] = None


class InvestmentUpdate(BaseModel):
    asset_name: Optional[str] = Field(None, min_length=1, max_length=150)
    investment_type: Optional[str] = Field(None, min_length=1, max_length=50)
    quantity: Optional[Decimal] = Field(None, gt=0)
    current_value: Optional[Decimal] = Field(None, ge=0)


class InvestmentResponse(InvestmentBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
