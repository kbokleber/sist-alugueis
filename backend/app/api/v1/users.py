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
from app.services.audit_service import AuditService
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


@router.post("", response_model=ResponseWrapper[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    service = UserService(db)
    try:
        user = await service.create(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CREATE",
        entity_type="user",
        entity_id=user.id,
        new_values={
            "full_name": user.full_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        },
    )

    return ResponseWrapper(data=user, message="User created successfully")


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

    # Capture old values before update
    old_values = {
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    }

    updated = await service.update(user, data.model_dump(exclude_unset=True))

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="user",
        entity_id=user_id,
        old_values=old_values,
        new_values=data.model_dump(exclude_unset=True),
    )

    return ResponseWrapper(data=updated)


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    if str(current_user.id) == str(user_id):
        raise HTTPException(status_code=400, detail="You cannot delete your own user")

    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_values = {
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    }

    try:
        await service.delete(user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="DELETE",
        entity_type="user",
        entity_id=user_id,
        old_values=old_values,
    )

    return {"message": "User deleted successfully"}


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

    # Audit log for password change
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="user_password",
        entity_id=user_id,
        new_values={"action": "password_changed"},
    )

    return {"message": "Password changed successfully"}
