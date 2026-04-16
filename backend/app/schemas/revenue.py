from __future__ import annotations
import uuid
from datetime import datetime, date as date_type
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RevenueBase(BaseModel):
    property_id: uuid.UUID
    year_month: str
    date: date_type
    checkin_date: Optional[date_type] = None
    checkout_date: Optional[date_type] = None
    guest_name: str
    listing_name: Optional[str] = None
    listing_source: Optional[str] = None
    nights: int
    gross_amount: float | None = None
    cleaning_fee: float = 0
    platform_fee: float = 0
    net_amount: float
    pending_amount: float | None = None
    is_pending: bool | None = None
    payment_status: str | None = None
    pending_text: str | None = None
    external_id: Optional[str] = None
    notes: Optional[str] = None


class RevenueCreate(RevenueBase):
    pass


class RevenueUpdate(BaseModel):
    property_id: uuid.UUID | None = None
    year_month: str | None = None
    date: date_type | None = None
    checkin_date: date_type | None = None
    checkout_date: date_type | None = None
    guest_name: str | None = None
    listing_name: str | None = None
    listing_source: str | None = None
    nights: int | None = None
    gross_amount: float | None = None
    cleaning_fee: float | None = None
    platform_fee: float | None = None
    net_amount: float | None = None
    pending_amount: float | None = None
    is_pending: bool | None = None
    payment_status: str | None = None
    pending_text: str | None = None
    external_id: str | None = None
    notes: str | None = None


class RevenueResponse(RevenueBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    property_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class RevenueSummary(BaseModel):
    year_month: str
    total_gross: float
    total_net: float
    total_nights: int
    total_bookings: int
    total_cleaning: float
    total_platform_fee: float
