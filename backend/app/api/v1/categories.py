import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    ResponseWrapper,
)
from app.services.category_service import CategoryService
from app.services.audit_service import AuditService
from app.dependencies import get_current_user
from app.models import User, CategoryType


router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=ResponseWrapper[list[CategoryResponse]])
async def list_categories(
    type: CategoryType | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    categories = await service.get_all(current_user.id, type)
    return ResponseWrapper(data=categories)


@router.post("", response_model=ResponseWrapper[CategoryResponse], status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    category = await service.create(current_user.id, data.model_dump())

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CREATE",
        entity_type="category",
        entity_id=category.id,
        new_values=data.model_dump(),
    )

    return ResponseWrapper(data=category, message="Category created successfully")


@router.get("/{category_id}", response_model=ResponseWrapper[CategoryResponse])
async def get_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    category = await service.get_by_id(category_id, current_user.id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return ResponseWrapper(data=category)


@router.put("/{category_id}", response_model=ResponseWrapper[CategoryResponse])
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    category = await service.get_by_id(category_id, current_user.id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Capture old values before update
    old_values = {
        "name": category.name,
        "type": category.type.value if hasattr(category.type, 'value') else str(category.type),
        "is_active": category.is_active,
    }

    updated = await service.update(category, data.model_dump(exclude_unset=True))

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="category",
        entity_id=category_id,
        old_values=old_values,
        new_values=data.model_dump(exclude_unset=True),
    )

    return ResponseWrapper(data=updated)


@router.delete("/{category_id}")
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    category = await service.get_by_id(category_id, current_user.id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Capture old values before delete
    old_values = {
        "name": category.name,
        "type": category.type.value if hasattr(category.type, 'value') else str(category.type),
        "is_active": category.is_active,
    }

    try:
        await service.delete(category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="DELETE",
        entity_type="category",
        entity_id=category_id,
        old_values=old_values,
    )

    return {"message": "Category deleted successfully"}
