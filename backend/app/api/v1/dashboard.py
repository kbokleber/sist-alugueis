import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    DashboardOverview,
    PropertyDashboardData,
    ChartBarData,
    ChartPieData,
    ResponseWrapper,
)
from app.services.dashboard_service import DashboardService
from app.services.property_service import PropertyService
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=ResponseWrapper[DashboardOverview])
async def get_overview(
    year_month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DashboardService(db)
    overview = await service.get_overview(current_user.id, year_month)
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
    prop = await prop_service.get_by_id(property_id, current_user.id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    service = DashboardService(db)
    data = await service.get_property_dashboard(current_user.id, property_id, year_month)
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
    prop = await prop_service.get_by_id(property_id, current_user.id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    service = DashboardService(db)
    data = await service.get_bar_chart_data(current_user.id, property_id, months)
    return ResponseWrapper(data=data)


@router.get("/chart/bar", response_model=ResponseWrapper[ChartBarData])
async def get_bar_chart(
    property_id: uuid.UUID | None = Query(None),
    months: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DashboardService(db)
    data = await service.get_bar_chart_data(current_user.id, property_id, months)
    return ResponseWrapper(data=data)


@router.get("/chart/pie", response_model=ResponseWrapper[ChartPieData])
async def get_pie_chart(
    property_id: uuid.UUID = Query(...),
    year_month: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DashboardService(db)
    data = await service.get_pie_chart_data(current_user.id, property_id, year_month)
    return ResponseWrapper(data=data)


@router.get("/timeline")
async def get_timeline(
    property_id: uuid.UUID | None = Query(None),
    months: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DashboardService(db)
    data = await service.get_bar_chart_data(current_user.id, property_id, months)
    return ResponseWrapper(data=data)
