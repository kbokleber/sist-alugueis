import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import InventoryCategory, Property, PropertyInventoryItem


def _clean_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class InventoryItemService:
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
        self, item_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> PropertyInventoryItem | None:
        query = (
            select(PropertyInventoryItem)
            .options(
                selectinload(PropertyInventoryItem.category),
                selectinload(PropertyInventoryItem.property),
            )
            .where(PropertyInventoryItem.id == item_id)
        )
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()
        if item is None:
            return None
        if user_id is not None and item.property.user_id != user_id:
            return None
        return item

    async def get_all_for_property(
        self,
        property_id: uuid.UUID,
        category_id: uuid.UUID | None = None,
        q: str | None = None,
        include_inactive: bool = False,
    ) -> list[PropertyInventoryItem]:
        query = (
            select(PropertyInventoryItem)
            .options(selectinload(PropertyInventoryItem.category))
            .where(PropertyInventoryItem.property_id == property_id)
        )
        if not include_inactive:
            query = query.where(PropertyInventoryItem.is_active == True)  # noqa: E712
        if category_id is not None:
            query = query.where(PropertyInventoryItem.category_id == category_id)
        if q:
            term = f"%{q.strip()}%"
            query = query.where(
                or_(
                    PropertyInventoryItem.name.ilike(term),
                    PropertyInventoryItem.serial_number.ilike(term),
                    PropertyInventoryItem.brand.ilike(term),
                    PropertyInventoryItem.model.ilike(term),
                    PropertyInventoryItem.color.ilike(term),
                )
            )
        query = query.order_by(PropertyInventoryItem.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        prop: Property,
        data: dict,
        user_id: uuid.UUID | None = None,
    ) -> PropertyInventoryItem:
        category = await self._get_category(data["category_id"], property_id=prop.id)
        if category is None or not category.is_active:
            raise ValueError("Categoria de inventário não encontrada neste imóvel")

        item = PropertyInventoryItem(
            property_id=prop.id,
            category_id=category.id,
            name=data["name"].strip(),
            quantity_expected=data.get("quantity_expected", 1),
            color=_clean_optional_str(data.get("color")),
            serial_number=_clean_optional_str(data.get("serial_number")),
            brand=_clean_optional_str(data.get("brand")),
            model=_clean_optional_str(data.get("model")),
            image_url=_clean_optional_str(data.get("image_url")),
            notes=_clean_optional_str(data.get("notes")),
            is_consumable=bool(data.get("is_consumable", False)),
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item, attribute_names=["category"])
        return item

    async def update(
        self,
        item: PropertyInventoryItem,
        data: dict,
        user_id: uuid.UUID | None = None,
    ) -> PropertyInventoryItem:
        if "category_id" in data and data["category_id"] is not None:
            category = await self._get_category(
                data["category_id"], property_id=item.property_id
            )
            if category is None or not category.is_active:
                raise ValueError("Categoria de inventário não encontrada neste imóvel")
            item.category_id = category.id

        if "name" in data and data["name"] is not None:
            item.name = data["name"].strip()
        if "quantity_expected" in data and data["quantity_expected"] is not None:
            item.quantity_expected = data["quantity_expected"]
        if "color" in data:
            item.color = _clean_optional_str(data.get("color"))
        if "serial_number" in data:
            item.serial_number = _clean_optional_str(data.get("serial_number"))
        if "brand" in data:
            item.brand = _clean_optional_str(data.get("brand"))
        if "model" in data:
            item.model = _clean_optional_str(data.get("model"))
        if "image_url" in data:
            item.image_url = _clean_optional_str(data.get("image_url"))
        if "notes" in data:
            item.notes = _clean_optional_str(data.get("notes"))
        if "is_consumable" in data and data["is_consumable"] is not None:
            item.is_consumable = bool(data["is_consumable"])
        if "is_active" in data and data["is_active"] is not None:
            item.is_active = data["is_active"]

        await self.db.commit()
        await self.db.refresh(item, attribute_names=["category"])
        return item

    async def delete(self, item: PropertyInventoryItem) -> None:
        item.is_active = False
        await self.db.commit()

    async def _get_category(
        self, category_id: uuid.UUID, property_id: uuid.UUID
    ) -> InventoryCategory | None:
        result = await self.db.execute(
            select(InventoryCategory).where(
                InventoryCategory.id == category_id,
                InventoryCategory.property_id == property_id,
            )
        )
        return result.scalar_one_or_none()
