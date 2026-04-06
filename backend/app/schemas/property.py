import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class PropertyBase(BaseModel):
    name: str
    address: str | None = None
    property_value: float
    monthly_depreciation_percent: float = 1.00


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    property_value: float | None = None
    monthly_depreciation_percent: float | None = None
    is_active: bool | None = None


class PropertyResponse(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class PropertySummary(BaseModel):
    id: uuid.UUID
    name: str
    property_value: float
    monthly_depreciation_percent: float
    total_revenue: float = 0
    total_expenses: float = 0
    net_result: float = 0
    total_nights: int = 0
    total_bookings: int = 0
