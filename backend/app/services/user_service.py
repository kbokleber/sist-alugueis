import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserPasswordChange
from app.utils.security import verify_password, hash_password


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, data: UserCreate) -> User:
        existing_user = await self.get_by_email(data.email)
        if existing_user:
            raise ValueError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            is_superuser=data.is_superuser,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        has_related_data = any(
            (
                getattr(user, "properties", []),
                getattr(user, "categories", []),
                getattr(user, "revenues", []),
                getattr(user, "expenses", []),
                getattr(user, "audit_logs", []),
            )
        )
        if has_related_data:
            raise ValueError("User has related data and cannot be deleted")

        await self.db.delete(user)
        await self.db.commit()

    async def change_password(
        self,
        user: User,
        data: UserPasswordChange,
        require_current_password: bool = True,
    ) -> bool:
        if require_current_password and (
            not data.current_password
            or not verify_password(data.current_password, user.hashed_password)
        ):
            return False
        user.hashed_password = hash_password(data.new_password)
        await self.db.commit()
        return True
