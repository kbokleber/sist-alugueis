import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    full_name: str


class UserCreate(UserBase):
    password: str
    is_superuser: bool = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserPasswordChange(BaseModel):
    current_password: str | None = None
    new_password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserMeResponse(UserResponse):
    pass
