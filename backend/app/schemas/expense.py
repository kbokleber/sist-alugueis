import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.property_expense import ExpenseStatus


class ExpenseBase(BaseModel):
    property_id: uuid.UUID
    category_id: uuid.UUID
    year_month: str
    name: str
    amount: float
    is_reserve: bool = False
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    status: ExpenseStatus = ExpenseStatus.PENDING
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    property_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    year_month: Optional[str] = None
    name: Optional[str] = None
    amount: float | None = None
    is_reserve: bool | None = None
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    status: ExpenseStatus | None = None
    notes: Optional[str] = None


class ExpensePayPatch(BaseModel):
    paid_date: date
    status: ExpenseStatus = ExpenseStatus.PAID


class ExpenseResponse(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    property_code: Optional[str] = None
    property_name: Optional[str] = None
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ExpenseByCategory(BaseModel):
    category_id: uuid.UUID
    category_name: str
    category_color: Optional[str]
    total: float
    count: int
