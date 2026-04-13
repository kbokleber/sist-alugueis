from datetime import date, timedelta
from decimal import Decimal
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models import (
    CategoryType,
    ExpenseSource,
    ExpenseStatus,
    FinancialCategory,
    Property,
    PropertyExpense,
    RentalRevenue,
    User,
)
from app.services.dashboard_service import DashboardService


@pytest.mark.asyncio
async def test_get_overview_includes_pending_receivables():
    engine = create_async_engine("sqlite+aiosqlite:///./test_dashboard.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db_session:
        user = User(
            id=uuid.uuid4(),
            email="dashboard@test.com",
            hashed_password="hashed",
            full_name="Dashboard Test",
            is_active=True,
            is_superuser=False,
        )
        property_item = Property(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Casa Teste",
            property_value=Decimal("250000.00"),
            monthly_depreciation_percent=Decimal("1.00"),
            is_active=True,
        )
        revenue = RentalRevenue(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=property_item.id,
            year_month="2026-04",
            date=date(2026, 4, 15),
            guest_name="Hospede Teste",
            nights=4,
            gross_amount=Decimal("1200.00"),
            cleaning_fee=Decimal("100.00"),
            platform_fee=Decimal("50.00"),
            net_amount=Decimal("1050.00"),
            pending_amount=Decimal("320.00"),
        )

        db_session.add(user)
        db_session.add(property_item)
        db_session.add(revenue)
        await db_session.commit()

        service = DashboardService(db_session)
        overview = await service.get_overview(user.id, "2026-04", "2026-04")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    assert overview["total_pending_receivables"] == 320.0
    assert overview["properties"][0]["pending_receivables"] == 320.0
    assert overview["properties"][0]["occupied_today"] is False
    assert overview["properties"][0]["last_guest_name"] == "Hospede Teste"
    assert overview["properties"][0]["last_checkin_date"] is None
    assert overview["properties"][0]["last_checkout_date"] is None
    assert overview["properties"][0]["last_nights"] == 4


@pytest.mark.asyncio
async def test_get_bar_chart_data_includes_pending_receivables_dataset():
    engine = create_async_engine("sqlite+aiosqlite:///./test_dashboard_chart.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db_session:
        user = User(
            id=uuid.uuid4(),
            email="chart@test.com",
            hashed_password="hashed",
            full_name="Chart Test",
            is_active=True,
            is_superuser=False,
        )
        property_item = Property(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Apartamento Teste",
            property_value=Decimal("300000.00"),
            monthly_depreciation_percent=Decimal("1.00"),
            is_active=True,
        )
        revenue = RentalRevenue(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=property_item.id,
            year_month="2026-05",
            date=date(2026, 5, 10),
            guest_name="Hospede Chart",
            nights=3,
            gross_amount=Decimal("900.00"),
            cleaning_fee=Decimal("80.00"),
            platform_fee=Decimal("40.00"),
            net_amount=Decimal("780.00"),
            pending_amount=Decimal("150.00"),
        )
        category = FinancialCategory(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Manutenção",
            type=CategoryType.EXPENSE,
            color="#ef4444",
            icon="wrench",
            is_system=True,
        )
        script_expense = PropertyExpense(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=property_item.id,
            category_id=category.id,
            year_month="2026-05",
            name="Despesa script",
            amount=Decimal("300.00"),
            status=ExpenseStatus.PAID,
            source=ExpenseSource.SCRIPT,
        )
        manual_expense = PropertyExpense(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=property_item.id,
            category_id=category.id,
            year_month="2026-05",
            name="Despesa manual",
            amount=Decimal("120.00"),
            status=ExpenseStatus.PAID,
            source=ExpenseSource.MANUAL,
        )

        db_session.add(user)
        db_session.add(property_item)
        db_session.add(revenue)
        db_session.add(category)
        db_session.add(script_expense)
        db_session.add(manual_expense)
        await db_session.commit()

        service = DashboardService(db_session)
        chart_data = await service.get_bar_chart_data(user.id, property_item.id, "2026-05", "2026-05")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    assert chart_data["labels"] == ["mai/26"]
    assert chart_data["datasets"][0]["label"] == "Receitas"
    assert chart_data["datasets"][0]["data"] == [780.0]
    assert chart_data["datasets"][1]["label"] == "Pendências"
    assert chart_data["datasets"][1]["data"] == [150.0]
    assert chart_data["datasets"][2]["label"] == "Despesas"
    assert chart_data["datasets"][2]["data"] == [420.0]


@pytest.mark.asyncio
async def test_get_overview_counts_all_expenses_and_tracks_script_expenses():
    engine = create_async_engine("sqlite+aiosqlite:///./test_dashboard_script_only.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db_session:
        user = User(
            id=uuid.uuid4(),
            email="dashboard-script@test.com",
            hashed_password="hashed",
            full_name="Dashboard Script Test",
            is_active=True,
            is_superuser=False,
        )
        property_item = Property(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Casa Script",
            property_value=Decimal("250000.00"),
            monthly_depreciation_percent=Decimal("1.00"),
            is_active=True,
        )
        category = FinancialCategory(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Outros",
            type=CategoryType.EXPENSE,
            color="#ef4444",
            icon="wallet",
            is_system=True,
        )
        revenue = RentalRevenue(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=property_item.id,
            year_month="2026-04",
            date=date(2026, 4, 10),
            guest_name="Hospede Script",
            nights=2,
            gross_amount=Decimal("600.00"),
            cleaning_fee=Decimal("20.00"),
            platform_fee=Decimal("10.00"),
            net_amount=Decimal("570.00"),
            pending_amount=Decimal("0.00"),
        )
        script_expense = PropertyExpense(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=property_item.id,
            category_id=category.id,
            year_month="2026-04",
            name="Despesa script",
            amount=Decimal("200.00"),
            status=ExpenseStatus.PAID,
            source=ExpenseSource.SCRIPT,
        )
        manual_expense = PropertyExpense(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=property_item.id,
            category_id=category.id,
            year_month="2026-04",
            name="Despesa manual",
            amount=Decimal("150.00"),
            status=ExpenseStatus.PAID,
            source=ExpenseSource.MANUAL,
        )

        db_session.add_all([user, property_item, category, revenue, script_expense, manual_expense])
        await db_session.commit()

        service = DashboardService(db_session)
        overview = await service.get_overview(user.id, "2026-04", "2026-04")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    assert overview["total_expenses"] == 350.0
    assert overview["total_script_expenses"] == 200.0
    assert overview["properties"][0]["total_expenses"] == 350.0
    assert overview["properties"][0]["script_expenses"] == 200.0
    assert overview["total_net_result"] == 220.0


@pytest.mark.asyncio
async def test_get_overview_includes_current_occupancy_and_last_reservation():
    engine = create_async_engine("sqlite+aiosqlite:///./test_dashboard_occupancy.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    today = date.today()
    async with async_session() as db_session:
        user = User(
            id=uuid.uuid4(),
            email="occupancy@test.com",
            hashed_password="hashed",
            full_name="Occupancy Test",
            is_active=True,
            is_superuser=False,
        )
        occupied_property = Property(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Casa Ocupada",
            property_value=Decimal("400000.00"),
            monthly_depreciation_percent=Decimal("1.00"),
            is_active=True,
        )
        vacant_property = Property(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Casa Livre",
            property_value=Decimal("350000.00"),
            monthly_depreciation_percent=Decimal("1.00"),
            is_active=True,
        )
        current_revenue = RentalRevenue(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=occupied_property.id,
            year_month=today.strftime("%Y-%m"),
            date=today,
            checkin_date=today - timedelta(days=1),
            checkout_date=today + timedelta(days=2),
            guest_name="Hospede Atual",
            nights=3,
            gross_amount=Decimal("1000.00"),
            cleaning_fee=Decimal("50.00"),
            platform_fee=Decimal("20.00"),
            net_amount=Decimal("930.00"),
            pending_amount=Decimal("0.00"),
        )
        past_revenue = RentalRevenue(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=vacant_property.id,
            year_month=(today - timedelta(days=40)).strftime("%Y-%m"),
            date=today - timedelta(days=40),
            checkin_date=today - timedelta(days=45),
            checkout_date=today - timedelta(days=40),
            guest_name="Hospede Anterior",
            nights=5,
            gross_amount=Decimal("1200.00"),
            cleaning_fee=Decimal("60.00"),
            platform_fee=Decimal("30.00"),
            net_amount=Decimal("1110.00"),
            pending_amount=Decimal("0.00"),
        )

        db_session.add_all([user, occupied_property, vacant_property, current_revenue, past_revenue])
        await db_session.commit()

        service = DashboardService(db_session)
        overview = await service.get_overview(user.id, today.strftime("%Y-%m"), today.strftime("%Y-%m"))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    properties = {item["name"]: item for item in overview["properties"]}

    assert properties["Casa Ocupada"]["occupied_today"] is True
    assert properties["Casa Ocupada"]["current_guest_name"] == "Hospede Atual"
    assert properties["Casa Ocupada"]["current_checkin_date"] == today - timedelta(days=1)
    assert properties["Casa Ocupada"]["current_checkout_date"] == today + timedelta(days=2)
    assert properties["Casa Ocupada"]["current_nights"] == 3
    assert properties["Casa Ocupada"]["last_guest_name"] == "Hospede Atual"
    assert properties["Casa Ocupada"]["last_nights"] == 3

    assert properties["Casa Livre"]["occupied_today"] is False
    assert properties["Casa Livre"]["current_guest_name"] is None
    assert properties["Casa Livre"]["current_nights"] is None
    assert properties["Casa Livre"]["last_guest_name"] == "Hospede Anterior"
    assert properties["Casa Livre"]["last_checkin_date"] == today - timedelta(days=45)
    assert properties["Casa Livre"]["last_checkout_date"] == today - timedelta(days=40)
    assert properties["Casa Livre"]["last_nights"] == 5
