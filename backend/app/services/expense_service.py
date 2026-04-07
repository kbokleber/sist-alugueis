import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import PropertyExpense, FinancialCategory


class ExpenseService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def create(self, user_id: uuid.UUID, data: dict) -> PropertyExpense:
        expense = PropertyExpense(user_id=user_id, **data)
        self.db.add(expense)
        await self.db.commit()
        await self.db.refresh(expense)
        return expense

    async def update(self, expense: PropertyExpense, data: dict) -> PropertyExpense:
        for field, value in data.items():
            if value is not None:
                setattr(expense, field, value)
        await self.db.commit()
        await self.db.refresh(expense)
        return expense

    async def delete(self, expense: PropertyExpense) -> None:
        await self.db.delete(expense)
        await self.db.commit()

    async def mark_paid(self, expense: PropertyExpense, paid_date) -> PropertyExpense:
        from app.models.property_expense import ExpenseStatus
        expense.status = ExpenseStatus.PAID
        expense.paid_date = paid_date
        await self.db.commit()
        await self.db.refresh(expense)
        return expense

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
