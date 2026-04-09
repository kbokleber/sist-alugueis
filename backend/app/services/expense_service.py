import uuid
import calendar
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import PropertyExpense, FinancialCategory
from app.models.property_expense import ExpenseStatus


class ExpenseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _reload_with_relations(self, expense: PropertyExpense) -> PropertyExpense:
        expense_id = getattr(expense, "id", None)
        if expense_id is None:
            return expense

        user_id = getattr(expense, "user_id", None)
        reloaded = await self.get_by_id(expense_id, user_id)
        return reloaded or expense

    @staticmethod
    def _normalize_name(name: str | None, is_recurring: bool) -> str:
        prefix = "[Recorrente]"
        normalized_name = (name or "").strip()

        if normalized_name.startswith(prefix):
            normalized_name = normalized_name[len(prefix):].strip()

        if is_recurring:
            return f"{prefix} {normalized_name}".strip()

        return normalized_name or "Despesa"

    @staticmethod
    def _shift_date(source_date: date, months_to_add: int) -> date:
        total_months = (source_date.year * 12) + (source_date.month - 1) + months_to_add
        year = total_months // 12
        month = (total_months % 12) + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    @classmethod
    def _generate_occurrence_dates(
        cls,
        recurrence_type: str,
        start_date: date,
        end_date: date,
    ) -> list[date]:
        if end_date < start_date:
            raise ValueError("Recurrence end date must be greater than or equal to start date")

        step_months = 1 if recurrence_type == "MONTHLY" else 12
        dates: list[date] = []
        step_index = 0
        current_date = start_date

        while current_date <= end_date:
            dates.append(current_date)
            step_index += 1
            current_date = cls._shift_date(start_date, step_months * step_index)

        return dates

    @classmethod
    def build_create_payloads(cls, data: dict) -> list[dict]:
        payload = dict(data)
        is_recurring = payload.pop("is_recurring", False)
        recurrence_type = payload.pop("recurrence_type", None)
        recurrence_start_date = payload.pop("recurrence_start_date", None)
        recurrence_end_date = payload.pop("recurrence_end_date", None)
        payload["name"] = cls._normalize_name(payload.get("name"), is_recurring)

        if is_recurring:
            if recurrence_type not in {"MONTHLY", "ANNUAL"}:
                raise ValueError("Recurrence type must be MONTHLY or ANNUAL")
            if recurrence_start_date is None or recurrence_end_date is None:
                raise ValueError("Recurrence start and end dates are required")

            occurrence_dates = cls._generate_occurrence_dates(
                recurrence_type,
                recurrence_start_date,
                recurrence_end_date,
            )

            payloads: list[dict] = []
            for occurrence_date in occurrence_dates:
                item = dict(payload)
                item["year_month"] = occurrence_date.strftime("%Y-%m")
                item["due_date"] = occurrence_date
                item["status"] = ExpenseStatus.PENDING
                item["paid_date"] = None
                payloads.append(item)
            return payloads

        if payload.get("year_month") is None:
            due_date = payload.get("due_date")
            if due_date is None:
                raise ValueError("year_month is required for non-recurring expenses")
            payload["year_month"] = due_date.strftime("%Y-%m")

        return [payload]

    async def get_by_id(self, expense_id: uuid.UUID, user_id: uuid.UUID | None = None) -> PropertyExpense | None:
        query = (
            select(PropertyExpense)
            .options(
                selectinload(PropertyExpense.property),
                selectinload(PropertyExpense.category),
            )
            .where(PropertyExpense.id == expense_id)
        )
        if user_id is not None:
            query = query.where(PropertyExpense.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        user_id: uuid.UUID | None,
        property_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        year_month: str | None = None,
        start_month: str | None = None,
        end_month: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[PropertyExpense], int]:
        query = select(PropertyExpense).options(
            selectinload(PropertyExpense.property),
            selectinload(PropertyExpense.category),
        )
        count_query = select(func.count(PropertyExpense.id))

        if user_id is not None:
            query = query.where(PropertyExpense.user_id == user_id)
            count_query = count_query.where(PropertyExpense.user_id == user_id)

        if property_id:
            query = query.where(PropertyExpense.property_id == property_id)
            count_query = count_query.where(PropertyExpense.property_id == property_id)
        if category_id:
            query = query.where(PropertyExpense.category_id == category_id)
            count_query = count_query.where(PropertyExpense.category_id == category_id)
        if year_month:
            query = query.where(PropertyExpense.year_month == year_month)
            count_query = count_query.where(PropertyExpense.year_month == year_month)
        if start_month:
            query = query.where(PropertyExpense.year_month >= start_month)
            count_query = count_query.where(PropertyExpense.year_month >= start_month)
        if end_month:
            query = query.where(PropertyExpense.year_month <= end_month)
            count_query = count_query.where(PropertyExpense.year_month <= end_month)
        if status:
            query = query.where(PropertyExpense.status == status)
            count_query = count_query.where(PropertyExpense.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(PropertyExpense.due_date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def create(self, user_id: uuid.UUID, data: dict) -> list[PropertyExpense]:
        expenses = [
            PropertyExpense(user_id=user_id, **payload)
            for payload in self.build_create_payloads(data)
        ]
        self.db.add_all(expenses)
        await self.db.commit()
        expense_ids = [expense.id for expense in expenses]
        result = await self.db.execute(
            select(PropertyExpense)
            .options(
                selectinload(PropertyExpense.property),
                selectinload(PropertyExpense.category),
            )
            .where(PropertyExpense.id.in_(expense_ids))
        )
        expenses_by_id = {expense.id: expense for expense in result.scalars().all()}
        return [expenses_by_id[expense_id] for expense_id in expense_ids if expense_id in expenses_by_id]

    async def update(self, expense: PropertyExpense, data: dict) -> PropertyExpense:
        for field, value in data.items():
            if value is not None:
                setattr(expense, field, value)
        await self.db.commit()
        await self.db.refresh(expense)
        return await self._reload_with_relations(expense)

    async def delete(self, expense: PropertyExpense) -> None:
        await self.db.delete(expense)
        await self.db.commit()

    async def set_status(
        self,
        expense: PropertyExpense,
        status: ExpenseStatus,
        paid_date: date | None = None,
    ) -> PropertyExpense:
        expense.status = status
        expense.paid_date = paid_date or date.today() if status == ExpenseStatus.PAID else None
        await self.db.commit()
        await self.db.refresh(expense)
        return await self._reload_with_relations(expense)

    async def get_by_category(
        self,
        user_id: uuid.UUID | None,
        year_month: str | None = None,
        property_id: uuid.UUID | None = None,
    ) -> list[dict]:
        query = select(
            FinancialCategory.id.label("category_id"),
            FinancialCategory.name.label("category_name"),
            FinancialCategory.color.label("category_color"),
            func.coalesce(func.sum(PropertyExpense.amount), 0).label("total"),
            func.count(PropertyExpense.id).label("count"),
        ).join(
            PropertyExpense, PropertyExpense.category_id == FinancialCategory.id
        ).where(
            FinancialCategory.type == "EXPENSE",
        )

        if user_id is not None:
            query = query.where(PropertyExpense.user_id == user_id)

        if year_month:
            query = query.where(PropertyExpense.year_month == year_month)
        if property_id:
            query = query.where(PropertyExpense.property_id == property_id)

        query = query.group_by(
            FinancialCategory.id, FinancialCategory.name, FinancialCategory.color
        )

        result = await self.db.execute(query)
        return [dict(row._mapping) for row in result.all()]
