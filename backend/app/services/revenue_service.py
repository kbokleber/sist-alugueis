import uuid
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import RentalRevenue


class RevenueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @classmethod
    def _calculate_gross_amount(
        cls,
        net_amount: float | int,
        cleaning_fee: float | int = 0,
        platform_fee: float | int = 0,
    ) -> float:
        return float(net_amount or 0) + float(cleaning_fee or 0) + float(platform_fee or 0)

    @classmethod
    def _get_reference_date(cls, checkin_date: date | None, fallback_date: date) -> date:
        if checkin_date is not None and 2000 <= checkin_date.year <= 2100:
            return checkin_date
        return fallback_date

    @classmethod
    def _calculate_year_month(cls, reference_date: date) -> str:
        year = reference_date.year
        month = reference_date.month + 1
        if month == 13:
            year += 1
            month = 1
        return f"{year}-{month:02d}"

    async def get_by_id(self, revenue_id: uuid.UUID, user_id: uuid.UUID | None = None) -> RentalRevenue | None:
        query = (
            select(RentalRevenue)
            .options(selectinload(RentalRevenue.property))
            .where(RentalRevenue.id == revenue_id)
        )
        if user_id is not None:
            query = query.where(RentalRevenue.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        user_id: uuid.UUID | None,
        property_id: uuid.UUID | None = None,
        year_month: str | None = None,
        start_month: str | None = None,
        end_month: str | None = None,
        listing_source: str | None = None,
        external_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[RentalRevenue], int]:
        query = select(RentalRevenue).options(selectinload(RentalRevenue.property))
        count_query = select(func.count(RentalRevenue.id))

        if user_id is not None:
            query = query.where(RentalRevenue.user_id == user_id)
            count_query = count_query.where(RentalRevenue.user_id == user_id)

        if property_id:
            query = query.where(RentalRevenue.property_id == property_id)
            count_query = count_query.where(RentalRevenue.property_id == property_id)
        if year_month:
            query = query.where(RentalRevenue.year_month == year_month)
            count_query = count_query.where(RentalRevenue.year_month == year_month)
        if start_month:
            query = query.where(RentalRevenue.year_month >= start_month)
            count_query = count_query.where(RentalRevenue.year_month >= start_month)
        if end_month:
            query = query.where(RentalRevenue.year_month <= end_month)
            count_query = count_query.where(RentalRevenue.year_month <= end_month)
        if listing_source:
            query = query.where(RentalRevenue.listing_source == listing_source)
            count_query = count_query.where(RentalRevenue.listing_source == listing_source)
        if external_id:
            external_id_term = f"%{external_id.strip()}%"
            query = query.where(RentalRevenue.external_id.ilike(external_id_term))
            count_query = count_query.where(RentalRevenue.external_id.ilike(external_id_term))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(RentalRevenue.date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def create(self, user_id: uuid.UUID, data: dict) -> RentalRevenue:
        reference_date = self._get_reference_date(data.get("checkin_date"), data.get("date"))
        if reference_date is not None:
            data["year_month"] = self._calculate_year_month(reference_date)
        data["gross_amount"] = self._calculate_gross_amount(
            data.get("net_amount", 0),
            data.get("cleaning_fee", 0),
            data.get("platform_fee", 0),
        )
        revenue = RentalRevenue(user_id=user_id, **data)
        self.db.add(revenue)
        await self.db.commit()
        await self.db.refresh(revenue)
        return revenue

    async def update(self, revenue: RentalRevenue, data: dict) -> RentalRevenue:
        provided_year_month = data.get("year_month")
        if not provided_year_month:
            reference_date = self._get_reference_date(
                data.get("checkin_date", revenue.checkin_date),
                data.get("date", revenue.date),
            )
            if reference_date is not None:
                data["year_month"] = self._calculate_year_month(reference_date)
        if data.get("gross_amount") is None and any(
            field in data for field in ("net_amount", "cleaning_fee", "platform_fee")
        ):
            data["gross_amount"] = self._calculate_gross_amount(
                data.get("net_amount", revenue.net_amount),
                data.get("cleaning_fee", revenue.cleaning_fee),
                data.get("platform_fee", revenue.platform_fee),
            )
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
        user_id: uuid.UUID | None,
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
        )

        if user_id is not None:
            query = query.where(RentalRevenue.user_id == user_id)

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
