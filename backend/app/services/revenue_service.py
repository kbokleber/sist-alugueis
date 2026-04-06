import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import RentalRevenue


class RevenueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, revenue_id: uuid.UUID, user_id: uuid.UUID) -> RentalRevenue | None:
        result = await self.db.execute(
            select(RentalRevenue).where(
                RentalRevenue.id == revenue_id,
                RentalRevenue.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        user_id: uuid.UUID,
        property_id: uuid.UUID | None = None,
        year_month: str | None = None,
        listing_source: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[RentalRevenue], int]:
        query = select(RentalRevenue).where(RentalRevenue.user_id == user_id)
        count_query = select(func.count(RentalRevenue.id)).where(RentalRevenue.user_id == user_id)

        if property_id:
            query = query.where(RentalRevenue.property_id == property_id)
            count_query = count_query.where(RentalRevenue.property_id == property_id)
        if year_month:
            query = query.where(RentalRevenue.year_month == year_month)
            count_query = count_query.where(RentalRevenue.year_month == year_month)
        if listing_source:
            query = query.where(RentalRevenue.listing_source == listing_source)
            count_query = count_query.where(RentalRevenue.listing_source == listing_source)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(RentalRevenue.date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def create(self, user_id: uuid.UUID, data: dict) -> RentalRevenue:
        revenue = RentalRevenue(user_id=user_id, **data)
        self.db.add(revenue)
        await self.db.commit()
        await self.db.refresh(revenue)
        return revenue

    async def update(self, revenue: RentalRevenue, data: dict) -> RentalRevenue:
        for field, value in data.items():
            if value is not None:
                setattr(revenue, field, value)
        await self.db.commit()
        await self.db.refresh(revenue)
        return revenue

    async def delete(self, revenue: RentalRevenue) -> None:
        await self.db.delete(revenue)
        await self.db.commit()

    async def get_summary(
        self,
        user_id: uuid.UUID,
        property_id: uuid.UUID | None = None,
        year_month: str | None = None,
    ) -> dict:
        query = select(
            func.coalesce(func.sum(RentalRevenue.gross_amount), 0).label("total_gross"),
            func.coalesce(func.sum(RentalRevenue.net_amount), 0).label("total_net"),
            func.coalesce(func.sum(RentalRevenue.nights), 0).label("total_nights"),
            func.count(RentalRevenue.id).label("total_bookings"),
            func.coalesce(func.sum(RentalRevenue.cleaning_fee), 0).label("total_cleaning"),
            func.coalesce(func.sum(RentalRevenue.platform_fee), 0).label("total_platform_fee"),
        ).where(RentalRevenue.user_id == user_id)

        if property_id:
            query = query.where(RentalRevenue.property_id == property_id)
        if year_month:
            query = query.where(RentalRevenue.year_month == year_month)

        result = await self.db.execute(query)
        row = result.one()
        return {
            "year_month": year_month or "all",
            "total_gross": float(row.total_gross or 0),
            "total_net": float(row.total_net or 0),
            "total_nights": row.total_nights or 0,
            "total_bookings": row.total_bookings or 0,
            "total_cleaning": float(row.total_cleaning or 0),
            "total_platform_fee": float(row.total_platform_fee or 0),
        }
