import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import MonthlyClosing, ClosingStatus, RentalRevenue, PropertyExpense, Property
from decimal import Decimal


class ClosingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_closing(
        self, user_id: uuid.UUID, property_id: uuid.UUID, year_month: str
    ) -> MonthlyClosing | None:
        result = await self.db.execute(
            select(MonthlyClosing).where(
                MonthlyClosing.user_id == user_id,
                MonthlyClosing.property_id == property_id,
                MonthlyClosing.year_month == year_month,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, user_id: uuid.UUID, property_id: uuid.UUID | None = None,
        skip: int = 0, limit: int = 100,
    ) -> tuple[list[MonthlyClosing], int]:
        query = select(MonthlyClosing).where(MonthlyClosing.user_id == user_id)
        count_query = select(func.count(MonthlyClosing.id)).where(MonthlyClosing.user_id == user_id)

        if property_id:
            query = query.where(MonthlyClosing.property_id == property_id)
            count_query = count_query.where(MonthlyClosing.property_id == property_id)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(MonthlyClosing.year_month.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def generate_closing(
        self, user_id: uuid.UUID, property_id: uuid.UUID, year_month: str
    ) -> MonthlyClosing:
        # Get property info
        prop_result = await self.db.execute(select(Property).where(Property.id == property_id))
        prop = prop_result.scalar_one_or_none()
        if not prop:
            raise ValueError("Property not found")

        # Aggregate revenues
        rev_result = await self.db.execute(
            select(
                func.coalesce(func.sum(RentalRevenue.gross_amount), 0).label("total_revenue"),
                func.coalesce(func.sum(RentalRevenue.net_amount), 0).label("net_revenue"),
                func.coalesce(func.sum(RentalRevenue.nights), 0).label("total_nights"),
                func.count(RentalRevenue.id).label("total_bookings"),
                func.coalesce(func.sum(RentalRevenue.cleaning_fee), 0).label("cleaning_total"),
                func.coalesce(func.sum(RentalRevenue.platform_fee), 0).label("platform_fee_total"),
            ).where(
                RentalRevenue.user_id == user_id,
                RentalRevenue.property_id == property_id,
                RentalRevenue.year_month == year_month,
            )
        )
        rev = rev_result.one()

        # Aggregate expenses (excluding cleaning and platform fee from revenue)
        exp_result = await self.db.execute(
            select(
                func.coalesce(func.sum(PropertyExpense.amount), 0).label("total_expenses"),
            ).where(
                PropertyExpense.user_id == user_id,
                PropertyExpense.property_id == property_id,
                PropertyExpense.year_month == year_month,
            )
        )
        exp = exp_result.one()

        # Calculate depreciation (1% annual / 12 months)
        depreciation = float(prop.property_value) * (float(prop.monthly_depreciation_percent) / 100)

        # Other expenses = total expenses - (cleaning + platform fee already counted separately)
        other_expenses = float(exp.total_expenses or 0)

        total_revenue = float(rev.total_revenue or 0)
        total_expenses = float(exp.total_expenses or 0)
        net_result = float(rev.net_revenue or 0) - total_expenses - depreciation

        # Check if closing already exists
        existing = await self.get_closing(user_id, property_id, year_month)
        if existing:
            existing.total_revenue = Decimal(str(total_revenue))
            existing.total_expenses = Decimal(str(total_expenses))
            existing.net_result = Decimal(str(net_result))
            existing.total_nights = rev.total_nights or 0
            existing.total_bookings = rev.total_bookings or 0
            existing.depreciation_value = Decimal(str(depreciation))
            existing.cleaning_total = Decimal(str(rev.cleaning_total or 0))
            existing.platform_fee_total = Decimal(str(rev.platform_fee_total or 0))
            existing.other_expenses = Decimal(str(other_expenses))
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        closing = MonthlyClosing(
            user_id=user_id,
            property_id=property_id,
            year_month=year_month,
            total_revenue=Decimal(str(total_revenue)),
            total_expenses=Decimal(str(total_expenses)),
            net_result=Decimal(str(net_result)),
            total_nights=rev.total_nights or 0,
            total_bookings=rev.total_bookings or 0,
            depreciation_value=Decimal(str(depreciation)),
            cleaning_total=Decimal(str(rev.cleaning_total or 0)),
            platform_fee_total=Decimal(str(rev.platform_fee_total or 0)),
            other_expenses=Decimal(str(other_expenses)),
            status=ClosingStatus.OPEN,
        )
        self.db.add(closing)
        await self.db.commit()
        await self.db.refresh(closing)
        return closing

    async def close_period(self, closing: MonthlyClosing) -> MonthlyClosing:
        closing.status = ClosingStatus.CLOSED
        closing.closed_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(closing)
        return closing

    async def reopen_period(self, closing: MonthlyClosing) -> MonthlyClosing:
        closing.status = ClosingStatus.OPEN
        closing.closed_at = None
        await self.db.commit()
        await self.db.refresh(closing)
        return closing
