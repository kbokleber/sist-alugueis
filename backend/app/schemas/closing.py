import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.monthly_closing import ClosingStatus


class ClosingBase(BaseModel):
    property_id: uuid.UUID
    year_month: str


class ClosingResponse(ClosingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    total_revenue: float
    total_expenses: float
    net_result: float
    total_nights: int
    total_bookings: int
    depreciation_value: float
    cleaning_total: float
    platform_fee_total: float
    other_expenses: float
    status: ClosingStatus
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ClosingGenerateRequest(BaseModel):
    property_id: uuid.UUID
    year_month: str


class ClosingNotesUpdate(BaseModel):
    notes: str
