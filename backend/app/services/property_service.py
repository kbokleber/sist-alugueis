import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property, RentalRevenue, PropertyExpense


class PropertyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, property_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Property | None:
        query = select(Property).where(Property.id == property_id)
        if user_id is not None:
            query = query.where(Property.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: uuid.UUID | None = None) -> list[Property]:
        query = select(Property).where(Property.is_active == True)
        if user_id is not None:
            query = query.where(Property.user_id == user_id)
        result = await self.db.execute(query.order_by(Property.name))
        return list(result.scalars().all())

    async def create(self, user_id: uuid.UUID, code: str | None, name: str, address: str | None,
                     property_value: float, monthly_depreciation_percent: float = 1.00) -> Property:
        prop = Property(
            user_id=user_id,
            code=code,
            name=name,
            address=address,
            property_value=property_value,
            monthly_depreciation_percent=monthly_depreciation_percent,
        )
        self.db.add(prop)
        await self.db.commit()
        await self.db.refresh(prop)
        return prop

    async def update(self, prop: Property, data: dict) -> Property:
        for field, value in data.items():
            if value is not None:
                setattr(prop, field, value)
        await self.db.commit()
        await self.db.refresh(prop)
        return prop

    async def delete(self, prop: Property) -> None:
        prop.is_active = False
        await self.db.commit()

    async def get_summary(self, prop: Property, year_month: str | None = None) -> dict:
        query_revenues = select(
            func.coalesce(func.sum(RentalRevenue.gross_amount), 0).label("total_revenue"),
            func.coalesce(func.sum(RentalRevenue.nights), 0).label("total_nights"),
            func.count(RentalRevenue.id).label("total_bookings"),
        ).where(RentalRevenue.property_id == prop.id)

        query_expenses = select(
            func.coalesce(func.sum(PropertyExpense.amount), 0).label("total_expenses"),
        ).where(PropertyExpense.property_id == prop.id)

        if year_month:
            query_revenues = query_revenues.where(RentalRevenue.year_month == year_month)
            query_expenses = query_expenses.where(PropertyExpense.year_month == year_month)

        rev_result = await self.db.execute(query_revenues)
        exp_result = await self.db.execute(query_expenses)

        rev_data = rev_result.one()
        exp_data = exp_result.one()

        return {
            "id": prop.id,
            "name": prop.name,
            "property_value": float(prop.property_value),
            "monthly_depreciation_percent": float(prop.monthly_depreciation_percent),
            "total_revenue": float(rev_data.total_revenue or 0),
            "total_expenses": float(exp_data.total_expenses or 0),
            "net_result": float(rev_data.total_revenue or 0) - float(exp_data.total_expenses or 0),
            "total_nights": rev_data.total_nights or 0,
            "total_bookings": rev_data.total_bookings or 0,
        }
