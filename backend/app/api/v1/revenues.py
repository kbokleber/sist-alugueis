import uuid
from datetime import date
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
from app.services.audit_service import AuditService
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(prefix="/revenues", tags=["revenues"])


def serialize_revenue(revenue) -> RevenueResponse:
    return RevenueResponse.model_validate(
        {
            "id": revenue.id,
            "user_id": revenue.user_id,
            "property_id": revenue.property_id,
            "property_name": revenue.property.name if revenue.property else None,
            "year_month": revenue.year_month,
            "date": revenue.date,
            "checkin_date": revenue.checkin_date,
            "checkout_date": revenue.checkout_date,
            "guest_name": revenue.guest_name,
            "listing_name": revenue.listing_name,
            "listing_source": revenue.listing_source,
            "nights": revenue.nights,
            "gross_amount": float(revenue.gross_amount),
            "cleaning_fee": float(revenue.cleaning_fee),
            "platform_fee": float(revenue.platform_fee),
            "net_amount": float(revenue.net_amount),
            "pending_amount": float(revenue.pending_amount) if revenue.pending_amount is not None else None,
            "external_id": revenue.external_id,
            "notes": revenue.notes,
            "created_at": revenue.created_at,
            "updated_at": revenue.updated_at,
        }
    )


@router.get("", response_model=ResponseWrapper[list[RevenueResponse]])
async def list_revenues(
    property_id: uuid.UUID | None = Query(None),
    year_month: str | None = Query(None),
    start_month: str | None = Query(None),
    end_month: str | None = Query(None),
    listing_source: str | None = Query(None),
    external_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    skip = (page - 1) * per_page
    revenues, total, totals = await service.get_all(
        user_id=scope_user_id,
        property_id=property_id,
        year_month=year_month,
        start_month=start_month,
        end_month=end_month,
        listing_source=listing_source,
        external_id=external_id,
        skip=skip,
        limit=per_page,
    )
    total_pages = (total + per_page - 1) // per_page
    return ResponseWrapper(
        data=[serialize_revenue(revenue) for revenue in revenues],
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "totals": totals,
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
    hydrated_revenue = await service.get_by_id(revenue.id, current_user.id)
    if hydrated_revenue is not None:
        revenue = hydrated_revenue

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CREATE",
        entity_type="revenue",
        entity_id=revenue.id,
        new_values=data.model_dump(),
    )

    return ResponseWrapper(data=serialize_revenue(revenue), message="Revenue created successfully")


@router.get("/summary", response_model=ResponseWrapper[RevenueSummary])
async def get_revenue_summary(
    property_id: uuid.UUID | None = Query(None),
    year_month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    summary = await service.get_summary(scope_user_id, property_id, year_month)
    return ResponseWrapper(data=summary)


@router.get("/calendar", response_model=ResponseWrapper[list[RevenueResponse]])
async def get_revenue_calendar(
    property_id: uuid.UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be less than or equal to end_date")

    service = RevenueService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    revenues = await service.get_calendar_reservations(scope_user_id, property_id, start_date, end_date)
    return ResponseWrapper(data=[serialize_revenue(revenue) for revenue in revenues])


@router.get("/{revenue_id}", response_model=ResponseWrapper[RevenueResponse])
async def get_revenue(
    revenue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    revenue = await service.get_by_id(revenue_id, scope_user_id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue not found")
    return ResponseWrapper(data=serialize_revenue(revenue))


@router.put("/{revenue_id}", response_model=ResponseWrapper[RevenueResponse])
async def update_revenue(
    revenue_id: uuid.UUID,
    data: RevenueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    revenue = await service.get_by_id(revenue_id, scope_user_id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue not found")

    # Capture old values before update
    old_values = {
        "property_id": str(revenue.property_id),
        "year_month": revenue.year_month,
        "date": revenue.date.isoformat(),
        "checkin_date": revenue.checkin_date.isoformat() if revenue.checkin_date else None,
        "checkout_date": revenue.checkout_date.isoformat() if revenue.checkout_date else None,
        "guest_name": revenue.guest_name,
        "listing_name": revenue.listing_name,
        "listing_source": revenue.listing_source,
        "nights": revenue.nights,
        "gross_amount": float(revenue.gross_amount),
        "cleaning_fee": float(revenue.cleaning_fee),
        "platform_fee": float(revenue.platform_fee),
        "net_amount": float(revenue.net_amount),
        "pending_amount": float(revenue.pending_amount) if revenue.pending_amount is not None else None,
        "external_id": revenue.external_id,
        "notes": revenue.notes,
    }

    updated = await service.update(revenue, data.model_dump(exclude_unset=True))
    hydrated_updated = await service.get_by_id(updated.id, scope_user_id)
    if hydrated_updated is not None:
        updated = hydrated_updated

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="revenue",
        entity_id=revenue_id,
        old_values=old_values,
        new_values=data.model_dump(exclude_unset=True),
    )

    return ResponseWrapper(data=serialize_revenue(updated))


@router.delete("/{revenue_id}")
async def delete_revenue(
    revenue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RevenueService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    revenue = await service.get_by_id(revenue_id, scope_user_id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue not found")

    # Capture old values before delete
    old_values = {
        "property_id": str(revenue.property_id),
        "year_month": revenue.year_month,
        "date": revenue.date.isoformat(),
        "checkin_date": revenue.checkin_date.isoformat() if revenue.checkin_date else None,
        "checkout_date": revenue.checkout_date.isoformat() if revenue.checkout_date else None,
        "guest_name": revenue.guest_name,
        "listing_name": revenue.listing_name,
        "listing_source": revenue.listing_source,
        "nights": revenue.nights,
        "gross_amount": float(revenue.gross_amount),
        "cleaning_fee": float(revenue.cleaning_fee),
        "platform_fee": float(revenue.platform_fee),
        "net_amount": float(revenue.net_amount),
        "pending_amount": float(revenue.pending_amount) if revenue.pending_amount is not None else None,
        "external_id": revenue.external_id,
        "notes": revenue.notes,
    }

    await service.delete(revenue)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="DELETE",
        entity_type="revenue",
        entity_id=revenue_id,
        old_values=old_values,
    )

    return {"message": "Revenue deleted successfully"}
