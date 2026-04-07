import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    DashboardOverview,
    PropertyDashboardData,
    ChartBarData,
    ChartPieData,
    DashboardKPIs,
    ResponseWrapper,
)
from app.services.dashboard_service import DashboardService
from app.services.property_service import PropertyService
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_month_range_from_count(months: int) -> tuple[str, str]:
    today = date.today()
    end_year = today.year
    end_month = today.month
    start_year = end_year
    start_month = end_month - (months - 1)

    while start_month <= 0:
        start_month += 12
        start_year -= 1

    return f"{start_year}-{start_month:02d}", f"{end_year}-{end_month:02d}"


@router.get("/overview", response_model=ResponseWrapper[DashboardOverview])
async def get_overview(
    start_month: str | None = Query(None),
    end_month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DashboardService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    overview = await service.get_overview(scope_user_id, start_month, end_month)
    return ResponseWrapper(data=overview)


@router.get("/property/{property_id}", response_model=ResponseWrapper[PropertyDashboardData])
async def get_property_dashboard(
    property_id: uuid.UUID,
    year_month: str = Query(..., description="Year-month in YYYY-MM format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify property belongs to user
    prop_service = PropertyService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await prop_service.get_by_id(property_id, scope_user_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    service = DashboardService(db)
    data = await service.get_property_dashboard(scope_user_id, property_id, year_month)
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this period")
    return ResponseWrapper(data=data)


@router.get("/property/{property_id}/monthly")
async def get_property_monthly(
    property_id: uuid.UUID,
    months: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop_service = PropertyService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await prop_service.get_by_id(property_id, scope_user_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    service = DashboardService(db)
    start_month, end_month = get_month_range_from_count(months)
    data = await service.get_bar_chart_data(scope_user_id, property_id, start_month, end_month)
    return ResponseWrapper(data=data)


@router.get("/chart/bar", response_model=ResponseWrapper[ChartBarData])
async def get_bar_chart(
    property_id: uuid.UUID | None = Query(None),
    start_month: str | None = Query(None),
    end_month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DashboardService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    data = await service.get_bar_chart_data(scope_user_id, property_id, start_month, end_month)
    return ResponseWrapper(data=data)


@router.get("/chart/pie", response_model=ResponseWrapper[ChartPieData])
async def get_pie_chart(
    property_id: uuid.UUID | None = Query(None),
    start_month: str | None = Query(None),
    end_month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DashboardService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    data = await service.get_pie_chart_data(scope_user_id, property_id, start_month, end_month)
    return ResponseWrapper(data=data)


@router.get("/timeline")
async def get_timeline(
    property_id: uuid.UUID | None = Query(None),
    months: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DashboardService(db)
    start_month, end_month = get_month_range_from_count(months)
    scope_user_id = None if current_user.is_superuser else current_user.id
    data = await service.get_bar_chart_data(scope_user_id, property_id, start_month, end_month)
    return ResponseWrapper(data=data)


@router.get("/kpis", response_model=ResponseWrapper[DashboardKPIs])
async def get_kpis(
    year_month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get main KPIs for dashboard"""
    service = DashboardService(db)
    kpis = await service.get_kpis(current_user.id, year_month)
    return ResponseWrapper(data=kpis)
