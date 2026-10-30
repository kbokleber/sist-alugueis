import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import InventoryCategory, Property, PropertyInventoryItem


class InventoryCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_property(
        self, property_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> Property | None:
        query = select(Property).where(Property.id == property_id)
        if user_id is not None:
            query = query.where(Property.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(
        self, category_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> InventoryCategory | None:
        query = (
            select(InventoryCategory)
            .options(selectinload(InventoryCategory.property))
            .where(InventoryCategory.id == category_id)
        )
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()
        if category is None:
            return None
        if user_id is not None and category.property.user_id != user_id:
            return None
        return category

    async def get_all_for_property(
        self,
        property_id: uuid.UUID,
        include_inactive: bool = False,
    ) -> list[InventoryCategory]:
        query = select(InventoryCategory).where(
            InventoryCategory.property_id == property_id
        )
        if not include_inactive:
            query = query.where(InventoryCategory.is_active == True)  # noqa: E712
        query = query.order_by(InventoryCategory.sort_order, InventoryCategory.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, property_id: uuid.UUID, data: dict) -> InventoryCategory:
        existing = await self.db.execute(
            select(InventoryCategory).where(
                InventoryCategory.property_id == property_id,
                func.lower(InventoryCategory.name) == data["name"].strip().lower(),
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Já existe uma categoria com este nome neste imóvel")

        category = InventoryCategory(
            property_id=property_id,
            name=data["name"].strip(),
            sort_order=data.get("sort_order", 0),
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category: InventoryCategory, data: dict) -> InventoryCategory:
        if "name" in data and data["name"] is not None:
            name = data["name"].strip()
            existing = await self.db.execute(
                select(InventoryCategory).where(
                    InventoryCategory.property_id == category.property_id,
                    func.lower(InventoryCategory.name) == name.lower(),
                    InventoryCategory.id != category.id,
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Já existe uma categoria com este nome neste imóvel")
            category.name = name

        if "sort_order" in data and data["sort_order"] is not None:
            category.sort_order = data["sort_order"]
        if "is_active" in data and data["is_active"] is not None:
            category.is_active = data["is_active"]

        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category: InventoryCategory) -> None:
        items_count = await self.db.execute(
            select(func.count())
            .select_from(PropertyInventoryItem)
            .where(
                PropertyInventoryItem.category_id == category.id,
                PropertyInventoryItem.is_active == True,  # noqa: E712
            )
        )
        if items_count.scalar_one() > 0:
            category.is_active = False
            await self.db.commit()
            return

        await self.db.delete(category)
        await self.db.commit()
