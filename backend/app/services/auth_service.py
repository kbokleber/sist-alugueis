import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.utils.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, login_data: LoginRequest) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(login_data.password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def register(self, data: RegisterRequest) -> User:
        hashed = hash_password(data.password)
        user = User(
            email=data.email,
            hashed_password=hashed,
            full_name=data.full_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    def create_tokens(self, user: User) -> TokenResponse:
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "is_superuser": user.is_superuser,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse | None:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            return None
        if payload.get("type") != "refresh":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            return None
        return self.create_tokens(user)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
