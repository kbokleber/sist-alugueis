import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertySummary,
    ResponseWrapper,
)
from app.services.property_service import PropertyService
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=ResponseWrapper[list[PropertyResponse]])
async def list_properties(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    properties = await service.get_all_for_user(current_user.id)
    return ResponseWrapper(data=properties)


@router.post("", response_model=ResponseWrapper[PropertyResponse], status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    prop = await service.create(
        user_id=current_user.id,
        name=data.name,
        address=data.address,
        property_value=data.property_value,
        monthly_depreciation_percent=data.monthly_depreciation_percent,
    )
    return ResponseWrapper(data=prop, message="Property created successfully")


@router.get("/{property_id}", response_model=ResponseWrapper[PropertyResponse])
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    prop = await service.get_by_id(property_id, current_user.id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return ResponseWrapper(data=prop)


@router.put("/{property_id}", response_model=ResponseWrapper[PropertyResponse])
async def update_property(
    property_id: uuid.UUID,
    data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    prop = await service.get_by_id(property_id, current_user.id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    updated = await service.update(prop, data.model_dump(exclude_unset=True))
    return ResponseWrapper(data=updated)


@router.delete("/{property_id}")
async def delete_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    prop = await service.get_by_id(property_id, current_user.id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    await service.delete(prop)
    return {"message": "Property deleted successfully"}


@router.get("/{property_id}/summary", response_model=ResponseWrapper[PropertySummary])
async def get_property_summary(
    property_id: uuid.UUID,
    year_month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    prop = await service.get_by_id(property_id, current_user.id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    summary = await service.get_summary(prop, year_month)
    return ResponseWrapper(data=summary)
