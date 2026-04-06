import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    RevenueCreate,
    RevenueUpdate,
    RevenueResponse,
    RevenueSummary,
    ResponseWrapper,
    PaginatedResponse,
)
from app.services.revenue_service import RevenueService
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(prefix="/revenues", tags=["revenues"])


@router.get("", response_model=ResponseWrapper[list[RevenueResponse]])
async def list_revenues(
    property_id: uuid.UUID | None = Query(None),
    year_month: str | None = Query(None),
    listing_source: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    skip = (page - 1) * per_page
    revenues, total = await service.get_all(
        user_id=current_user.id,
        property_id=property_id,
        year_month=year_month,
        listing_source=listing_source,
        skip=skip,
        limit=per_page,
    )
    total_pages = (total + per_page - 1) // per_page
    return ResponseWrapper(
        data=revenues,
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )


@router.post("", response_model=ResponseWrapper[RevenueResponse], status_code=status.HTTP_201_CREATED)
async def create_revenue(
    data: RevenueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    revenue = await service.create(current_user.id, data.model_dump())
    return ResponseWrapper(data=revenue, message="Revenue created successfully")


@router.get("/summary", response_model=ResponseWrapper[RevenueSummary])
async def get_revenue_summary(
    property_id: uuid.UUID | None = Query(None),
    year_month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    summary = await service.get_summary(current_user.id, property_id, year_month)
    return ResponseWrapper(data=summary)


@router.get("/{revenue_id}", response_model=ResponseWrapper[RevenueResponse])
async def get_revenue(
    revenue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    revenue = await service.get_by_id(revenue_id, current_user.id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue not found")
    return ResponseWrapper(data=revenue)


@router.put("/{revenue_id}", response_model=ResponseWrapper[RevenueResponse])
async def update_revenue(
    revenue_id: uuid.UUID,
    data: RevenueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    revenue = await service.get_by_id(revenue_id, current_user.id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue not found")

    updated = await service.update(revenue, data.model_dump(exclude_unset=True))
    return ResponseWrapper(data=updated)


@router.delete("/{revenue_id}")
async def delete_revenue(
    revenue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    revenue = await service.get_by_id(revenue_id, current_user.id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue not found")

    await service.delete(revenue)
    return {"message": "Revenue deleted successfully"}
