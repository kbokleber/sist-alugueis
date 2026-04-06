import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserPasswordChange,
    UserResponse,
    ResponseWrapper,
    PaginatedResponse,
)
from app.services.user_service import UserService
from app.dependencies import get_current_user, get_current_superuser
from app.models import User


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ResponseWrapper[list[UserResponse]])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    service = UserService(db)
    users = await service.get_all(skip=skip, limit=limit)
    return ResponseWrapper(data=users)


@router.get("/me", response_model=ResponseWrapper[UserResponse])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return ResponseWrapper(data=current_user)


@router.get("/{user_id}", response_model=ResponseWrapper[UserResponse])
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ResponseWrapper(data=user)


@router.put("/{user_id}", response_model=ResponseWrapper[UserResponse])
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if str(current_user.id) != str(user_id) and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = await service.update(user, data.model_dump(exclude_unset=True))
    return ResponseWrapper(data=updated)


@router.patch("/{user_id}/password")
async def change_password(
    user_id: uuid.UUID,
    data: UserPasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if str(current_user.id) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    success = await service.change_password(user, data)
    if not success:
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    return {"message": "Password changed successfully"}
