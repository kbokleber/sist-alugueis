import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    ResponseWrapper,
)
from app.services.audit_service import AuditService
from app.services.inventory_item_service import InventoryItemService

router = APIRouter(tags=["inventory-items"])


def _serialize_item(item) -> dict:
    return {
        "id": item.id,
        "property_id": item.property_id,
        "category_id": item.category_id,
        "name": item.name,
        "quantity_expected": item.quantity_expected,
        "color": item.color,
        "serial_number": item.serial_number,
        "brand": item.brand,
        "model": item.model,
        "image_url": item.image_url,
        "notes": item.notes,
        "is_consumable": bool(getattr(item, "is_consumable", False)),
        "is_active": item.is_active,
        "category_name": item.category.name if item.category else None,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get(
    "/properties/{property_id}/inventory-items",
    response_model=ResponseWrapper[list[InventoryItemResponse]],
)
async def list_inventory_items(
    property_id: uuid.UUID,
    category_id: uuid.UUID | None = Query(None),
    q: str | None = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryItemService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await service.get_property(property_id, scope_user_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    items = await service.get_all_for_property(
        property_id,
        category_id=category_id,
        q=q,
        include_inactive=include_inactive,
    )
    return ResponseWrapper(data=[_serialize_item(item) for item in items])


@router.post(
    "/properties/{property_id}/inventory-items",
    response_model=ResponseWrapper[InventoryItemResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_inventory_item(
    property_id: uuid.UUID,
    data: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryItemService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    prop = await service.get_property(property_id, scope_user_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    try:
        item = await service.create(prop, data.model_dump(), user_id=prop.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CREATE",
        entity_type="inventory_item",
        entity_id=item.id,
        new_values={**data.model_dump(mode="json"), "property_id": str(property_id)},
    )
    return ResponseWrapper(data=_serialize_item(item), message="Item de inventário criado")


@router.put(
    "/inventory-items/{item_id}",
    response_model=ResponseWrapper[InventoryItemResponse],
)
async def update_inventory_item(
    item_id: uuid.UUID,
    data: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryItemService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    item = await service.get_by_id(item_id, scope_user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventário não encontrado")

    old_values = {
        "name": item.name,
        "category_id": str(item.category_id),
        "quantity_expected": item.quantity_expected,
        "color": item.color,
        "serial_number": item.serial_number,
        "brand": item.brand,
        "model": item.model,
        "image_url": item.image_url,
        "notes": item.notes,
        "is_active": item.is_active,
    }
    try:
        updated = await service.update(
            item, data.model_dump(exclude_unset=True), user_id=item.property.user_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="inventory_item",
        entity_id=item_id,
        old_values=old_values,
        new_values=data.model_dump(exclude_unset=True, mode="json"),
    )
    return ResponseWrapper(data=_serialize_item(updated))


@router.delete("/inventory-items/{item_id}")
async def delete_inventory_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryItemService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    item = await service.get_by_id(item_id, scope_user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventário não encontrado")

    old_values = {
        "name": item.name,
        "category_id": str(item.category_id),
        "quantity_expected": item.quantity_expected,
        "is_active": item.is_active,
    }
    await service.delete(item)

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="DELETE",
        entity_type="inventory_item",
        entity_id=item_id,
        old_values=old_values,
    )
    return {"message": "Item de inventário removido"}
