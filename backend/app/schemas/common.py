from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar, Optional


T = TypeVar("T")


class ResponseWrapper(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    data: T
    message: Optional[str] = None
    meta: Optional[dict] = None


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    data: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    errors: Optional[list] = None
