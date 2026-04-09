import uuid
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property, RentalRevenue, PropertyExpense, ExpenseStatus


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _exclude_cancelled_expenses(query):
        return query.where(PropertyExpense.status != ExpenseStatus.CANCELLED)

    @staticmethod
    def _apply_month_range(query, model, start_month: str | None = None, end_month: str | None = None):
        if start_month:
            query = query.where(model.year_month >= start_month)
        if end_month:
            query = query.where(model.year_month <= end_month)
        return query

    @staticmethod
    def _iter_months(start_month: str, end_month: str) -> list[str]:
        start_year, start_mon = map(int, start_month.split("-"))
        end_year, end_mon = map(int, end_month.split("-"))

        current_year = start_year
        current_mon = start_mon
        months: list[str] = []

        while (current_year, current_mon) <= (end_year, end_mon):
            months.append(f"{current_year}-{current_mon:02d}")
            current_mon += 1
            if current_mon > 12:
                current_mon = 1
                current_year += 1

        return months

    @staticmethod
    def _last_n_months_range(months: int) -> tuple[str, str]:
        today = date.today()
        end_year = today.year
        end_month = today.month
        start_year = end_year
        start_mon = end_month - (months - 1)

        while start_mon <= 0:
            start_mon += 12
            start_year -= 1

        return f"{start_year}-{start_mon:02d}", f"{end_year}-{end_month:02d}"

    async def get_overview(
        self, user_id: uuid.UUID | None, start_month: str | None = None, end_month: str | None = None
    ) -> dict:
        # Get all properties
        props_query = select(Property).where(Property.is_active == True)
        if user_id is not None:
            props_query = props_query.where(Property.user_id == user_id)
        props_result = await self.db.execute(props_query)
        properties = list(props_result.scalars().all())

        total_revenue = 0.0
        total_expenses = 0.0
        total_pending_receivables = 0.0
        total_nights = 0
        total_bookings = 0
        property_summaries = []

        for prop in properties:
            # Revenues
            rev_query = select(
                func.coalesce(func.sum(RentalRevenue.net_amount), 0).label("rev"),
                func.coalesce(func.sum(RentalRevenue.pending_amount), 0).label("pending"),
                func.coalesce(func.sum(RentalRevenue.nights), 0).label("nights"),
                func.count(RentalRevenue.id).label("bookings"),
            ).where(RentalRevenue.property_id == prop.id)

            exp_query = select(
                func.coalesce(func.sum(PropertyExpense.amount), 0).label("exp"),
            ).where(PropertyExpense.property_id == prop.id)
            exp_query = self._exclude_cancelled_expenses(exp_query)

            if user_id is not None:
                rev_query = rev_query.where(RentalRevenue.user_id == user_id)
                exp_query = exp_query.where(PropertyExpense.user_id == user_id)

            rev_query = self._apply_month_range(rev_query, RentalRevenue, start_month, end_month)
            exp_query = self._apply_month_range(exp_query, PropertyExpense, start_month, end_month)

            rev_res = await self.db.execute(rev_query)
            exp_res = await self.db.execute(exp_query)

            rev_data = rev_res.one()
            exp_data = exp_res.one()

            rev_total = float(rev_data.rev or 0)
            pending_total = float(rev_data.pending or 0)
            exp_total = float(exp_data.exp or 0)
            prop_nights = rev_data.nights or 0
            prop_bookings = rev_data.bookings or 0

            total_revenue += rev_total
            total_expenses += exp_total
            total_pending_receivables += pending_total
            total_nights += prop_nights
            total_bookings += prop_bookings

            net_result = rev_total - exp_total

            property_summaries.append({
                "id": prop.id,
                "name": prop.name,
                "total_revenue": rev_total,
                "total_expenses": exp_total,
                "net_result": net_result,
                "pending_receivables": pending_total,
                "total_nights": prop_nights,
                "total_bookings": prop_bookings,
            })

        total_net_result = sum(p["net_result"] for p in property_summaries)

        default_month = date.today().strftime("%Y-%m")
        return {
            "start_month": start_month or default_month,
            "end_month": end_month or start_month or default_month,
            "total_properties": len(properties),
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "total_net_result": total_net_result,
            "total_pending_receivables": total_pending_receivables,
            "total_nights": total_nights,
            "total_bookings": total_bookings,
            "properties": property_summaries,
        }

    async def get_property_dashboard(
        self, user_id: uuid.UUID | None, property_id: uuid.UUID, year_month: str
    ) -> dict | None:
        prop_query = select(Property).where(Property.id == property_id)
        if user_id is not None:
            prop_query = prop_query.where(Property.user_id == user_id)
        prop_result = await self.db.execute(prop_query)
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
                RentalRevenue.property_id == property_id,
                RentalRevenue.year_month == year_month,
            )
        )
        if user_id is not None:
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
            self._exclude_cancelled_expenses(
                select(func.coalesce(func.sum(PropertyExpense.amount), 0).label("total_expenses")).where(
                    PropertyExpense.property_id == property_id,
                    PropertyExpense.year_month == year_month,
                )
            )
        )
        if user_id is not None:
            exp_result = await self.db.execute(
                self._exclude_cancelled_expenses(
                    select(func.coalesce(func.sum(PropertyExpense.amount), 0).label("total_expenses")).where(
                        PropertyExpense.user_id == user_id,
                        PropertyExpense.property_id == property_id,
                        PropertyExpense.year_month == year_month,
                    )
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
        self,
        user_id: uuid.UUID | None,
        property_id: uuid.UUID | None = None,
        start_month: str | None = None,
        end_month: str | None = None,
    ) -> dict:
        default_month = date.today().strftime("%Y-%m")
        start_month = start_month or default_month
        end_month = end_month or start_month

        labels = []
        revenues_data = []
        pending_data = []
        expenses_data = []

        for ym in self._iter_months(start_month, end_month):
            month_date = date(int(ym[:4]), int(ym[5:7]), 1)
            labels.append(month_date.strftime("%b/%y"))

            # Revenue
            rev_q = select(
                func.coalesce(func.sum(RentalRevenue.net_amount), 0).label("revenue"),
                func.coalesce(func.sum(RentalRevenue.pending_amount), 0).label("pending"),
            ).where(
                RentalRevenue.year_month == ym,
            )
            if user_id is not None:
                rev_q = rev_q.where(RentalRevenue.user_id == user_id)
            if property_id:
                rev_q = rev_q.where(RentalRevenue.property_id == property_id)
            rev_res = await self.db.execute(rev_q)
            rev_row = rev_res.one()
            revenues_data.append(float(rev_row.revenue or 0))
            pending_data.append(float(rev_row.pending or 0))

            # Expenses
            exp_q = select(func.coalesce(func.sum(PropertyExpense.amount), 0)).where(
                PropertyExpense.year_month == ym,
            )
            exp_q = self._exclude_cancelled_expenses(exp_q)
            if user_id is not None:
                exp_q = exp_q.where(PropertyExpense.user_id == user_id)
            if property_id:
                exp_q = exp_q.where(PropertyExpense.property_id == property_id)
            exp_res = await self.db.execute(exp_q)
            expenses_data.append(float(exp_res.scalar() or 0))

        return {
            "labels": labels,
            "datasets": [
                {"label": "Receitas", "data": revenues_data},
                {"label": "Pendências", "data": pending_data},
                {"label": "Despesas", "data": expenses_data},
            ],
        }

    async def get_pie_chart_data(
        self,
        user_id: uuid.UUID | None,
        property_id: uuid.UUID | None,
        start_month: str | None,
        end_month: str | None,
    ) -> dict:
        from sqlalchemy import select
        from app.models import FinancialCategory

        query = (
            select(
                FinancialCategory.name,
                func.coalesce(func.sum(PropertyExpense.amount), 0).label("total"),
                FinancialCategory.color,
            )
            .join(PropertyExpense, PropertyExpense.category_id == FinancialCategory.id)
            .where(
                FinancialCategory.type == "EXPENSE",
            )
            .group_by(FinancialCategory.id, FinancialCategory.name, FinancialCategory.color)
        )
        if user_id is not None:
            query = query.where(PropertyExpense.user_id == user_id)
        query = self._exclude_cancelled_expenses(query)
        query = self._apply_month_range(query, PropertyExpense, start_month, end_month)

        if property_id:
            query = query.where(PropertyExpense.property_id == property_id)

        result = await self.db.execute(query)

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
        exp_query = self._exclude_cancelled_expenses(exp_query)
        
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
            "net_result": total_revenue - total_expenses,
            "total_nights": total_nights,
            "total_bookings": total_bookings,
            "average_booking_value": average_booking_value,
            "occupancy_rate": round(occupancy_rate, 1),
            "properties_count": len(properties),
            "top_property": top_property,
            "top_property_revenue": top_property_revenue,
        }
