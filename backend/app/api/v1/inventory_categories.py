import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    InventoryCategoryCreate,
    InventoryCategoryResponse,
    InventoryCategoryUpdate,
    ResponseWrapper,
)
from app.services.audit_service import AuditService
from app.services.inventory_category_service import InventoryCategoryService

router = APIRouter(tags=["inventory-categories"])


@router.get(
    "/properties/{property_id}/inventory-categories",
    response_model=ResponseWrapper[list[InventoryCategoryResponse]],
)
async def list_inventory_categories(
    property_id: uuid.UUID,
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryCategoryService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await service.get_property(property_id, scope_user_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    categories = await service.get_all_for_property(
        property_id, include_inactive=include_inactive
    )
    return ResponseWrapper(data=categories)


@router.post(
    "/properties/{property_id}/inventory-categories",
    response_model=ResponseWrapper[InventoryCategoryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_inventory_category(
    property_id: uuid.UUID,
    data: InventoryCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryCategoryService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await service.get_property(property_id, scope_user_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    try:
        category = await service.create(property_id, data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CREATE",
        entity_type="inventory_category",
        entity_id=category.id,
        new_values={**data.model_dump(), "property_id": str(property_id)},
    )
    return ResponseWrapper(data=category, message="Categoria de inventário criada")


@router.get(
    "/inventory-categories/{category_id}",
    response_model=ResponseWrapper[InventoryCategoryResponse],
)
async def get_inventory_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryCategoryService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    category = await service.get_by_id(category_id, scope_user_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria de inventário não encontrada")
    return ResponseWrapper(data=category)


@router.put(
    "/inventory-categories/{category_id}",
    response_model=ResponseWrapper[InventoryCategoryResponse],
)
async def update_inventory_category(
    category_id: uuid.UUID,
    data: InventoryCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryCategoryService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    category = await service.get_by_id(category_id, scope_user_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria de inventário não encontrada")

    old_values = {
        "name": category.name,
        "sort_order": category.sort_order,
        "is_active": category.is_active,
    }
    try:
        updated = await service.update(category, data.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="inventory_category",
        entity_id=category_id,
        old_values=old_values,
        new_values=data.model_dump(exclude_unset=True),
    )
    return ResponseWrapper(data=updated)


@router.delete("/inventory-categories/{category_id}")
async def delete_inventory_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryCategoryService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    category = await service.get_by_id(category_id, scope_user_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria de inventário não encontrada")

    old_values = {
        "name": category.name,
        "sort_order": category.sort_order,
        "is_active": category.is_active,
        "property_id": str(category.property_id),
    }
    await service.delete(category)

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="DELETE",
        entity_type="inventory_category",
        entity_id=category_id,
        old_values=old_values,
    )
    return {"message": "Categoria de inventário removida"}
