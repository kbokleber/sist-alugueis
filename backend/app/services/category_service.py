import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import FinancialCategory, CategoryType


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: uuid.UUID, user_id: uuid.UUID | None = None) -> FinancialCategory | None:
        query = select(FinancialCategory).where(FinancialCategory.id == category_id)
        if user_id is not None:
            query = query.where(FinancialCategory.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, user_id: uuid.UUID | None = None, type: CategoryType | None = None) -> list[FinancialCategory]:
        query = select(FinancialCategory)
        if user_id is not None:
            query = query.where(FinancialCategory.user_id == user_id)
        if type:
            query = query.where(FinancialCategory.type == type)
        query = query.order_by(FinancialCategory.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, user_id: uuid.UUID, data: dict) -> FinancialCategory:
        category = FinancialCategory(user_id=user_id, **data)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category: FinancialCategory, data: dict) -> FinancialCategory:
        for field, value in data.items():
            if value is not None:
                setattr(category, field, value)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category: FinancialCategory) -> None:
        if category.is_system:
            raise ValueError("System categories cannot be deleted")
        await self.db.delete(category)
        await self.db.commit()

    async def seed_default_categories(self, user_id: uuid.UUID) -> list[FinancialCategory]:
        defaults = [
            {"name": "Limpeza", "type": CategoryType.EXPENSE, "color": "#FF6B6B", "icon": "sparkles", "is_system": True},
            {"name": "Manutenção", "type": CategoryType.EXPENSE, "color": "#4ECDC4", "icon": "wrench", "is_system": True},
            {"name": "Taxa Administrativa", "type": CategoryType.EXPENSE, "color": "#45B7D1", "icon": "percent", "is_system": True},
            {"name": "Condomínio", "type": CategoryType.EXPENSE, "color": "#FFA07A", "icon": "building", "is_system": True},
            {"name": "IPTU", "type": CategoryType.EXPENSE, "color": "#98D8C8", "icon": "landmark", "is_system": True},
            {"name": "Taxa de Limpeza", "type": CategoryType.REVENUE, "color": "#A8E6CF", "icon": "sparkles", "is_system": True},
            {"name": "Aluguel", "type": CategoryType.REVENUE, "color": "#88D8B0", "icon": "home", "is_system": True},
            {"name": "Taxa Airbnb", "type": CategoryType.EXPENSE, "color": "#FF5E7D", "icon": "airbnb", "is_system": True},
            {"name": "Contas de Consumo", "type": CategoryType.EXPENSE, "color": "#F7DC6F", "icon": "zap", "is_system": True},
            {"name": "Outros", "type": CategoryType.EXPENSE, "color": "#BDBDBD", "icon": "more", "is_system": True},
        ]
        created = []
        for cat_data in defaults:
            existing = await self.db.execute(
                select(FinancialCategory).where(
                    FinancialCategory.user_id == user_id,
                    FinancialCategory.name == cat_data["name"],
                )
            )
            if existing.scalar_one_or_none() is None:
                cat = FinancialCategory(user_id=user_id, **cat_data)
                self.db.add(cat)
                created.append(cat)
        if created:
            await self.db.commit()
            for cat in created:
                await self.db.refresh(cat)
        return created
