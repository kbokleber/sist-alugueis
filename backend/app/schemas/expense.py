import uuid
from datetime import datetime, date
from typing import Optional
import enum
from pydantic import BaseModel, ConfigDict
from app.models.property_expense import ExpenseStatus, ExpenseSource


class ExpenseRecurrenceType(str, enum.Enum):
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"


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


class ExpenseCreate(BaseModel):
    property_id: uuid.UUID
    category_id: uuid.UUID
    year_month: Optional[str] = None
    name: str | None = None
    amount: float
    is_reserve: bool = False
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    status: ExpenseStatus = ExpenseStatus.PENDING
    source: ExpenseSource | None = None
    notes: Optional[str] = None
    is_recurring: bool = False
    recurrence_type: ExpenseRecurrenceType | None = None
    recurrence_start_date: date | None = None
    recurrence_end_date: date | None = None


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
    source: ExpenseSource | None = None
    notes: Optional[str] = None


class ExpensePayPatch(BaseModel):
    paid_date: date | None = None
    status: ExpenseStatus = ExpenseStatus.PAID


class ExpenseStatusPatch(BaseModel):
    status: ExpenseStatus
    paid_date: date | None = None


class ExpenseResponse(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    is_recurring: bool = False
    property_code: Optional[str] = None
    property_name: Optional[str] = None
    category_name: Optional[str] = None
    source: ExpenseSource
    created_at: datetime
    updated_at: Optional[datetime] = None


class ExpenseByCategory(BaseModel):
    category_id: uuid.UUID
    category_name: str
    category_color: Optional[str]
    total: float
    count: int
