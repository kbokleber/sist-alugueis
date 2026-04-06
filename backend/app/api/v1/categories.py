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

    updated = await service.update(category, data.model_dump(exclude_unset=True))
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

    try:
        await service.delete(category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Category deleted successfully"}
