import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    ClosingGenerateRequest,
    ClosingNotesUpdate,
    ClosingResponse,
    ResponseWrapper,
)
from app.services.closing_service import ClosingService
from app.services.property_service import PropertyService
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(prefix="/closing", tags=["closing"])


@router.get("", response_model=ResponseWrapper[list[ClosingResponse]])
async def list_closings(
    property_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClosingService(db)
    skip = (page - 1) * per_page
    closings, total = await service.get_all(
        user_id=current_user.id,
        property_id=property_id,
        skip=skip,
        limit=per_page,
    )
    total_pages = (total + per_page - 1) // per_page
    return ResponseWrapper(
        data=closings,
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )


@router.post("/generate", response_model=ResponseWrapper[ClosingResponse])
async def generate_closing(
    data: ClosingGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify property belongs to user
    prop_service = PropertyService(db)
    prop = await prop_service.get_by_id(data.property_id, current_user.id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    service = ClosingService(db)
    closing = await service.generate_closing(
        user_id=current_user.id,
        property_id=data.property_id,
        year_month=data.year_month,
    )
    return ResponseWrapper(data=closing, message="Closing generated successfully")


@router.get("/{property_id}/{year_month}", response_model=ResponseWrapper[ClosingResponse])
async def get_closing(
    property_id: uuid.UUID,
    year_month: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClosingService(db)
    closing = await service.get_closing(current_user.id, property_id, year_month)
    if not closing:
        raise HTTPException(status_code=404, detail="Closing not found")
    return ResponseWrapper(data=closing)


@router.post("/{property_id}/{year_month}/close", response_model=ResponseWrapper[ClosingResponse])
async def close_period(
    property_id: uuid.UUID,
    year_month: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClosingService(db)
    closing = await service.get_closing(current_user.id, property_id, year_month)
    if not closing:
        raise HTTPException(status_code=404, detail="Closing not found")

    updated = await service.close_period(closing)
    return ResponseWrapper(data=updated, message="Period closed successfully")


@router.post("/{property_id}/{year_month}/reopen", response_model=ResponseWrapper[ClosingResponse])
async def reopen_period(
    property_id: uuid.UUID,
    year_month: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClosingService(db)
    closing = await service.get_closing(current_user.id, property_id, year_month)
    if not closing:
        raise HTTPException(status_code=404, detail="Closing not found")

    updated = await service.reopen_period(closing)
    return ResponseWrapper(data=updated, message="Period reopened successfully")
