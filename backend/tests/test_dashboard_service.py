from datetime import date
from decimal import Decimal
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models import Property, RentalRevenue, User
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
