"""Financial Goal request and response schemas."""

import datetime
import uuid
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

PriorityType = Literal["low", "medium", "high"]


class GoalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Name or title of financial goal")
    target_amount: Decimal = Field(..., gt=0, description="Target savings amount")
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Current accumulated amount")
    target_date: datetime.date = Field(..., description="Target completion date")
    priority: PriorityType = Field(default="medium", description="Goal priority level")


class GoalCreate(GoalBase):
    user_id: Optional[uuid.UUID] = None


class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    target_amount: Optional[Decimal] = Field(None, gt=0)
    current_amount: Optional[Decimal] = Field(None, ge=0)
    target_date: Optional[datetime.date] = None
    priority: Optional[PriorityType] = None


class GoalResponse(GoalBase):
    id: uuid.UUID
    user_id: uuid.UUID
    progress_percentage: Decimal = Field(default=Decimal("0.00"), description="Calculated deterministic progress %")
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
