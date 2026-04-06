import uuid
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from app.models.property_expense import ExpenseStatus


class ExpenseBase(BaseModel):
    property_id: uuid.UUID
    category_id: uuid.UUID
    year_month: str
    name: str
    amount: float
    is_reserve: bool = False
    due_date: date | None = None
    paid_date: date | None = None
    status: ExpenseStatus = ExpenseStatus.PENDING
    notes: str | None = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    property_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    year_month: str | None = None
    name: str | None = None
    amount: float | None = None
    is_reserve: bool | None = None
    due_date: date | None = None
    paid_date: date | None = None
    status: ExpenseStatus | None = None
    notes: str | None = None


class ExpensePayPatch(BaseModel):
    paid_date: date
    status: ExpenseStatus = ExpenseStatus.PAID


class ExpenseResponse(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None


class ExpenseByCategory(BaseModel):
    category_id: uuid.UUID
    category_name: str
    category_color: str | None
    total: float
    count: int
