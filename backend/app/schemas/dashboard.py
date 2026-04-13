from __future__ import annotations

import uuid
from datetime import date
from pydantic import BaseModel, ConfigDict


class PropertyDashboard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    property_value: float


class PropertyDashboardData(BaseModel):
    property: PropertyDashboard
    year_month: str
    property_monthly_value: float
    months_owned: int
    one_percent: float
    total_revenue: float
    total_nights: int
    total_bookings: int
    net_revenue: float
    cleaning_total: float
    platform_fee_total: float
    other_expenses: float
    total_expenses: float
    gross_result: float
    net_result: float


class DashboardOverview(BaseModel):
    start_month: str
    end_month: str
    total_properties: int
    total_revenue: float
    total_expenses: float
    total_script_expenses: float
    total_net_result: float
    total_pending_receivables: float
    total_nights: int
    total_bookings: int
    properties: list[PropertySummaryItem]


class PropertySummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    total_revenue: float
    total_expenses: float
    script_expenses: float
    net_result: float
    pending_receivables: float
    total_nights: int
    total_bookings: int
    occupied_today: bool
    current_guest_name: str | None = None
    current_checkin_date: date | None = None
    current_checkout_date: date | None = None
    current_nights: int | None = None
    last_guest_name: str | None = None
    last_checkin_date: date | None = None
    last_checkout_date: date | None = None
    last_nights: int | None = None


class ChartBarData(BaseModel):
    labels: list[str]
    datasets: list[ChartDataset]


class ChartDataset(BaseModel):
    label: str
    data: list[float | None]


class ChartPieData(BaseModel):
    labels: list[str]
    datasets: list[ChartPieDataset]


class ChartPieDataset(BaseModel):
    data: list[float]
    backgroundColor: list[str]


class DashboardKPIs(BaseModel):
    """KPIs for dashboard overview"""
    total_revenue: float
    total_expenses: float
    net_result: float
    total_nights: int
    total_bookings: int
    average_booking_value: float
    occupancy_rate: float  # percentage
    properties_count: int
    top_property: str | None
    top_property_revenue: float
