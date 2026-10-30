import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.stay_checklist import (
    ChecklistItemCondition,
    ChecklistStatus,
    ChecklistType,
)


class InventoryCategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    sort_order: int = 0


class InventoryCategoryCreate(InventoryCategoryBase):
    pass


class InventoryCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class InventoryCategoryResponse(InventoryCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class InventoryItemBase(BaseModel):
    category_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    quantity_expected: int = Field(default=1, ge=1)
    color: Optional[str] = Field(default=None, max_length=100)
    serial_number: Optional[str] = Field(default=None, max_length=150)
    brand: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=150)
    image_url: Optional[str] = None
    notes: Optional[str] = None
    is_consumable: bool = False


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    quantity_expected: Optional[int] = Field(default=None, ge=1)
    color: Optional[str] = Field(default=None, max_length=100)
    serial_number: Optional[str] = Field(default=None, max_length=150)
    brand: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=150)
    image_url: Optional[str] = None
    notes: Optional[str] = None
    is_consumable: Optional[bool] = None
    is_active: Optional[bool] = None


class InventoryItemResponse(InventoryItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    is_active: bool
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ChecklistCreate(BaseModel):
    checklist_type: ChecklistType


class ChecklistItemUpdate(BaseModel):
    id: uuid.UUID
    quantity_found: Optional[int] = Field(default=None, ge=0)
    condition: Optional[ChecklistItemCondition] = None
    incident_notes: Optional[str] = None
    incident_image_url: Optional[str] = None


class ChecklistItemsUpdate(BaseModel):
    items: list[ChecklistItemUpdate]
    general_notes: Optional[str] = None


class ChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    checklist_id: uuid.UUID
    inventory_item_id: Optional[uuid.UUID] = None
    item_name: str
    category_name: str
    quantity_expected: int
    quantity_found: Optional[int] = None
    condition: ChecklistItemCondition
    incident_notes: Optional[str] = None
    incident_image_url: Optional[str] = None
    is_consumable: bool = False
    sort_order: int


class ChecklistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    rental_revenue_id: uuid.UUID
    checklist_type: ChecklistType
    status: ChecklistStatus
    performed_by_user_id: Optional[uuid.UUID] = None
    performed_by_name: Optional[str] = None
    performed_at: Optional[datetime] = None
    general_notes: Optional[str] = None
    has_incidents: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: list[ChecklistItemResponse] = []


class ChecklistSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    rental_revenue_id: uuid.UUID
    checklist_type: ChecklistType
    status: ChecklistStatus
    has_incidents: bool
    performed_by_name: Optional[str] = None
    performed_at: Optional[datetime] = None
