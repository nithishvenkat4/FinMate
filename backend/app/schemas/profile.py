"""Financial Profile request and response schemas."""

import datetime
import uuid
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

RiskPreferenceType = Literal["conservative", "moderate", "aggressive"]


class FinancialProfileBase(BaseModel):
    monthly_income: Decimal = Field(default=Decimal("0.00"), ge=0, description="Gross monthly income")
    monthly_fixed_expenses: Decimal = Field(default=Decimal("0.00"), ge=0, description="Monthly fixed expenses (rent, utilities, etc.)")
    current_savings: Decimal = Field(default=Decimal("0.00"), ge=0, description="Total current liquid savings")
    risk_preference: RiskPreferenceType = Field(default="moderate", description="User financial risk appetite")


class FinancialProfileCreate(FinancialProfileBase):
    user_id: Optional[uuid.UUID] = None


class FinancialProfileUpdate(BaseModel):
    monthly_income: Optional[Decimal] = Field(None, ge=0)
    monthly_fixed_expenses: Optional[Decimal] = Field(None, ge=0)
    current_savings: Optional[Decimal] = Field(None, ge=0)
    risk_preference: Optional[RiskPreferenceType] = None


class FinancialProfileResponse(FinancialProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
