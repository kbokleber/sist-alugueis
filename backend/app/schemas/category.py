import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.financial_category import CategoryType


class CategoryBase(BaseModel):
    name: str
    type: CategoryType
    color: str | None = None
    icon: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    type: CategoryType | None = None
    color: str | None = None
    icon: str | None = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    is_system: bool
    created_at: datetime
