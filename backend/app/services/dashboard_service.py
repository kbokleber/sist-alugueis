import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property, RentalRevenue, PropertyExpense, MonthlyClosing


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, user_id: uuid.UUID, year_month: str | None = None) -> dict:
        # Get all properties
        props_result = await self.db.execute(
            select(Property).where(Property.user_id == user_id, Property.is_active == True)
        )
        properties = list(props_result.scalars().all())

        total_revenue = 0.0
        total_expenses = 0.0
        total_nights = 0
        total_bookings = 0
        property_summaries = []

        for prop in properties:
            # Revenues
            rev_query = select(
                func.coalesce(func.sum(RentalRevenue.gross_amount), 0).label("rev"),
                func.coalesce(func.sum(RentalRevenue.net_amount), 0).label("net"),
                func.coalesce(func.sum(RentalRevenue.nights), 0).label("nights"),
                func.count(RentalRevenue.id).label("bookings"),
            ).where(RentalRevenue.user_id == user_id, RentalRevenue.property_id == prop.id)

            exp_query = select(
                func.coalesce(func.sum(PropertyExpense.amount), 0).label("exp"),
            ).where(PropertyExpense.user_id == user_id, PropertyExpense.property_id == prop.id)

            if year_month:
                rev_query = rev_query.where(RentalRevenue.year_month == year_month)
                exp_query = exp_query.where(PropertyExpense.year_month == year_month)

            rev_res = await self.db.execute(rev_query)
            exp_res = await self.db.execute(exp_query)

            rev_data = rev_res.one()
            exp_data = exp_res.one()

            rev_total = float(rev_data.rev or 0)
            net_rev = float(rev_data.net or 0)
            exp_total = float(exp_data.exp or 0)
            prop_nights = rev_data.nights or 0
            prop_bookings = rev_data.bookings or 0

            total_revenue += rev_total
            total_expenses += exp_total
            total_nights += prop_nights
            total_bookings += prop_bookings

            depreciation = float(prop.property_value) * (float(prop.monthly_depreciation_percent) / 100)
            net_result = net_rev - exp_total - depreciation

            property_summaries.append({
                "id": prop.id,
                "name": prop.name,
                "total_revenue": rev_total,
                "total_expenses": exp_total,
                "net_result": net_result,
                "total_nights": prop_nights,
                "total_bookings": prop_bookings,
            })

        total_net_result = sum(p["net_result"] for p in property_summaries)

        return {
            "year_month": year_month or datetime.utcnow().strftime("%Y-%m"),
            "total_properties": len(properties),
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "total_net_result": total_net_result,
            "total_nights": total_nights,
            "total_bookings": total_bookings,
            "properties": property_summaries,
        }

    async def get_property_dashboard(
        self, user_id: uuid.UUID, property_id: uuid.UUID, year_month: str
    ) -> dict | None:
        prop_result = await self.db.execute(
            select(Property).where(Property.id == property_id, Property.user_id == user_id)
        )
        prop = prop_result.scalar_one_or_none()
        if not prop:
            return None

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
        rev_data = rev_result.one()

        exp_result = await self.db.execute(
            select(func.coalesce(func.sum(PropertyExpense.amount), 0).label("total_expenses")).where(
                PropertyExpense.user_id == user_id,
                PropertyExpense.property_id == property_id,
                PropertyExpense.year_month == year_month,
            )
        )
        exp_total = float(exp_result.scalar() or 0)

        prop_value = float(prop.property_value)
        monthly_value = prop_value / 12
        depreciation = prop_value * (float(prop.monthly_depreciation_percent) / 100)
        net_revenue = float(rev_data.net_revenue or 0)
        other_expenses = exp_total
        total_expenses = other_expenses + float(rev_data.cleaning_total or 0) + float(rev_data.platform_fee_total or 0)
        gross_result = net_revenue - total_expenses
        net_result = gross_result - depreciation

        return {
            "property": {
                "id": prop.id,
                "name": prop.name,
                "property_value": prop_value,
            },
            "year_month": year_month,
            "property_monthly_value": monthly_value,
            "months_owned": 12,  # Simplified - could track actual purchase date
            "one_percent": prop_value * 0.01,
            "total_revenue": float(rev_data.total_revenue or 0),
            "total_nights": rev_data.total_nights or 0,
            "total_bookings": rev_data.total_bookings or 0,
            "net_revenue": net_revenue,
            "cleaning_total": float(rev_data.cleaning_total or 0),
            "platform_fee_total": float(rev_data.platform_fee_total or 0),
            "other_expenses": other_expenses,
            "total_expenses": total_expenses,
            "gross_result": gross_result,
            "net_result": net_result,
        }

    async def get_bar_chart_data(
        self, user_id: uuid.UUID, property_id: uuid.UUID | None = None, months: int = 12
    ) -> dict:
        # Get last N months
        from datetime import date, timedelta

        today = date.today()
        labels = []
        revenues_data = []
        expenses_data = []

        for i in range(months - 1, -1, -1):
            # Calculate month by subtracting 30 days approximately
            days_back = i * 30
            d = today - timedelta(days=days_back)
            ym = d.strftime("%Y-%m")
            labels.append(d.strftime("%b/%y"))

            # Revenue
            rev_q = select(func.coalesce(func.sum(RentalRevenue.gross_amount), 0)).where(
                RentalRevenue.user_id == user_id,
                RentalRevenue.year_month == ym,
            )
            if property_id:
                rev_q = rev_q.where(RentalRevenue.property_id == property_id)
            rev_res = await self.db.execute(rev_q)
            revenues_data.append(float(rev_res.scalar() or 0))

            # Expenses
            exp_q = select(func.coalesce(func.sum(PropertyExpense.amount), 0)).where(
                PropertyExpense.user_id == user_id,
                PropertyExpense.year_month == ym,
            )
            if property_id:
                exp_q = exp_q.where(PropertyExpense.property_id == property_id)
            exp_res = await self.db.execute(exp_q)
            expenses_data.append(float(exp_res.scalar() or 0))

        return {
            "labels": labels,
            "datasets": [
                {"label": "Receitas", "data": revenues_data},
                {"label": "Despesas", "data": expenses_data},
            ],
        }

    async def get_pie_chart_data(
        self, user_id: uuid.UUID, property_id: uuid.UUID, year_month: str
    ) -> dict:
        from sqlalchemy import select
        from app.models import FinancialCategory

        result = await self.db.execute(
            select(
                FinancialCategory.name,
                func.coalesce(func.sum(PropertyExpense.amount), 0).label("total"),
                FinancialCategory.color,
            )
            .join(PropertyExpense, PropertyExpense.category_id == FinancialCategory.id)
            .where(
                PropertyExpense.user_id == user_id,
                PropertyExpense.property_id == property_id,
                PropertyExpense.year_month == year_month,
                FinancialCategory.type == "EXPENSE",
            )
            .group_by(FinancialCategory.id, FinancialCategory.name, FinancialCategory.color)
        )

        rows = list(result.all())
        labels = [r.name for r in rows]
        data = [float(r.total) for r in rows]
        colors = [r.color or "#BDBDBD" for r in rows]

        return {
            "labels": labels,
            "datasets": [{"data": data, "backgroundColor": colors}],
        }

    async def get_kpis(self, user_id: uuid.UUID, year_month: str | None = None) -> dict:
        """Get main KPIs for dashboard"""
        from app.models import Property
        
        # Get all properties
        props_result = await self.db.execute(
            select(Property).where(Property.user_id == user_id, Property.is_active == True)
        )
        properties = list(props_result.scalars().all())
        
        # Calculate totals
        rev_query = select(
            func.coalesce(func.sum(RentalRevenue.gross_amount), 0).label("total_revenue"),
            func.coalesce(func.sum(RentalRevenue.net_amount), 0).label("net_revenue"),
            func.coalesce(func.sum(RentalRevenue.nights), 0).label("total_nights"),
            func.count(RentalRevenue.id).label("total_bookings"),
        ).where(RentalRevenue.user_id == user_id)
        
        exp_query = select(
            func.coalesce(func.sum(PropertyExpense.amount), 0).label("total_expenses"),
        ).where(PropertyExpense.user_id == user_id)
        
        if year_month:
            rev_query = rev_query.where(RentalRevenue.year_month == year_month)
            exp_query = exp_query.where(PropertyExpense.year_month == year_month)
        
        rev_res = await self.db.execute(rev_query)
        exp_res = await self.db.execute(exp_query)
        
        rev_data = rev_res.one()
        exp_data = exp_res.one()
        
        total_revenue = float(rev_data.total_revenue or 0)
        total_expenses = float(exp_data.total_expenses or 0)
        total_nights = rev_data.total_nights or 0
        total_bookings = rev_data.total_bookings or 0
        
        # Calculate average booking value
        average_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0
        
        # Find top property
        top_property = None
        top_property_revenue = 0
        if properties:
            for prop in properties:
                prop_rev_query = select(
                    func.coalesce(func.sum(RentalRevenue.gross_amount), 0).label("prop_rev")
                ).where(
                    RentalRevenue.user_id == user_id,
                    RentalRevenue.property_id == prop.id
                )
                if year_month:
                    prop_rev_query = prop_rev_query.where(RentalRevenue.year_month == year_month)
                prop_rev_res = await self.db.execute(prop_rev_query)
                prop_rev = float(prop_rev_res.scalar() or 0)
                if prop_rev > top_property_revenue:
                    top_property_revenue = prop_rev
                    top_property = prop.name
        
        # Calculate occupancy rate (simplified - based on max 30 nights per month)
        max_nights = len(properties) * 30
        occupancy_rate = (total_nights / max_nights * 100) if max_nights > 0 else 0
        
        return {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_result": float(rev_data.net_revenue or 0) - total_expenses,
            "total_nights": total_nights,
            "total_bookings": total_bookings,
            "average_booking_value": average_booking_value,
            "occupancy_rate": round(occupancy_rate, 1),
            "properties_count": len(properties),
            "top_property": top_property,
            "top_property_revenue": top_property_revenue,
        }
