from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    ResponseWrapper,
    UserMeResponse,
)
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ResponseWrapper[TokenResponse], status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    existing = await service.db.execute(
        __import__("sqlalchemy").select(User).where(User.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await service.register(data)
    tokens = service.create_tokens(user)
    return ResponseWrapper(data=tokens, message="User registered successfully")


@router.post("/login", response_model=ResponseWrapper[TokenResponse])
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = await service.authenticate(data)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    tokens = service.create_tokens(user)
    return ResponseWrapper(data=tokens)


@router.post("/refresh", response_model=ResponseWrapper[TokenResponse])
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    tokens = await service.refresh_tokens(data.refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return ResponseWrapper(data=tokens)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # In a production system, you would blacklist the refresh token here
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=ResponseWrapper[UserMeResponse])
async def get_me(current_user: User = Depends(get_current_user)):
    return ResponseWrapper(data=current_user)
