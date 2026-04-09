import base64
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertySummary,
    PropertyImageUploadResponse,
    ResponseWrapper,
)
from app.services.property_service import PropertyService
from app.services.audit_service import AuditService
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(prefix="/properties", tags=["properties"])
MAX_PROPERTY_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_PROPERTY_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.get("", response_model=ResponseWrapper[list[PropertyResponse]])
async def list_properties(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    properties = await service.get_all_for_user(scope_user_id)
    return ResponseWrapper(data=properties)


@router.post("/upload-image", response_model=ResponseWrapper[PropertyImageUploadResponse])
async def upload_property_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if image.content_type not in ALLOWED_PROPERTY_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Formato de imagem inválido. Use JPG, PNG ou WEBP.")

    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="Arquivo de imagem vazio.")
    if len(content) > MAX_PROPERTY_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="A imagem deve ter no máximo 5 MB.")

    encoded_content = base64.b64encode(content).decode("ascii")
    return ResponseWrapper(data={"image_url": f"data:{image.content_type};base64,{encoded_content}"})


@router.post("", response_model=ResponseWrapper[PropertyResponse], status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    prop = await service.create(
        user_id=current_user.id,
        code=data.code,
        name=data.name,
        address=data.address,
        image_url=data.image_url,
        property_value=data.property_value,
        monthly_depreciation_percent=data.monthly_depreciation_percent,
    )

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CREATE",
        entity_type="property",
        entity_id=prop.id,
        new_values=data.model_dump(),
    )

    return ResponseWrapper(data=prop, message="Property created successfully")


@router.get("/{property_id}", response_model=ResponseWrapper[PropertyResponse])
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await service.get_by_id(property_id, scope_user_id)
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
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await service.get_by_id(property_id, scope_user_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Capture old values before update
    old_values = {
        "code": prop.code,
        "name": prop.name,
        "address": prop.address,
        "image_url": prop.image_url,
        "property_value": float(prop.property_value),
        "monthly_depreciation_percent": float(prop.monthly_depreciation_percent) if prop.monthly_depreciation_percent else None,
        "is_active": prop.is_active,
    }

    updated = await service.update(prop, data.model_dump(exclude_unset=True))

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="property",
        entity_id=property_id,
        old_values=old_values,
        new_values=data.model_dump(exclude_unset=True),
    )

    return ResponseWrapper(data=updated)


@router.delete("/{property_id}")
async def delete_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await service.get_by_id(property_id, scope_user_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Capture old values before delete
    old_values = {
        "code": prop.code,
        "name": prop.name,
        "address": prop.address,
        "image_url": prop.image_url,
        "property_value": float(prop.property_value),
        "is_active": prop.is_active,
    }

    await service.delete(prop)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="DELETE",
        entity_type="property",
        entity_id=property_id,
        old_values=old_values,
    )

    return {"message": "Property deleted successfully"}


@router.get("/{property_id}/summary", response_model=ResponseWrapper[PropertySummary])
async def get_property_summary(
    property_id: uuid.UUID,
    year_month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PropertyService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await service.get_by_id(property_id, scope_user_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    summary = await service.get_summary(prop, year_month)
    return ResponseWrapper(data=summary)
