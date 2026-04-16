from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models import Property, RentalRevenue, User
from app.services.revenue_service import RevenueService


class FakeAsyncSession:
    def __init__(self):
        self.added = []
        self.commit_calls = 0
        self.refresh_calls = 0

    def add(self, instance):
        self.added.append(instance)

    async def commit(self):
        self.commit_calls += 1

    async def refresh(self, _instance):
        self.refresh_calls += 1


@pytest.mark.asyncio
async def test_create_revenue_calculates_gross_from_net_and_fees():
    session = FakeAsyncSession()
    service = RevenueService(session)

    revenue = await service.create(
        uuid.uuid4(),
        {
            "property_id": uuid.uuid4(),
            "year_month": "2026-04",
            "date": date(2026, 4, 10),
            "checkin_date": date(2026, 4, 8),
            "guest_name": "Hospede Teste",
            "nights": 3,
            "net_amount": 1000.0,
            "cleaning_fee": 150.0,
            "platform_fee": 50.0,
            "gross_amount": 1.0,
        },
    )

    assert float(revenue.gross_amount) == 1200.0
    assert revenue.year_month == "2026-05"
    assert session.commit_calls == 1
    assert session.refresh_calls == 1


@pytest.mark.asyncio
async def test_update_revenue_preserves_manual_gross_amount_when_provided():
    session = FakeAsyncSession()
    service = RevenueService(session)
    revenue = SimpleNamespace(
        checkin_date=date(2026, 4, 8),
        date=date(2026, 4, 10),
        gross_amount=Decimal("1200.00"),
        net_amount=Decimal("1000.00"),
        cleaning_fee=Decimal("150.00"),
        platform_fee=Decimal("50.00"),
    )

    updated = await service.update(
        revenue,
        {
            "net_amount": 900.0,
            "cleaning_fee": 100.0,
            "platform_fee": 50.0,
            "gross_amount": 1300.0,
        },
    )

    assert float(updated.gross_amount) == 1300.0
    assert float(updated.net_amount) == 900.0
    assert session.commit_calls == 1
    assert session.refresh_calls == 1


@pytest.mark.asyncio
async def test_update_revenue_recalculates_gross_when_missing_from_payload():
    session = FakeAsyncSession()
    service = RevenueService(session)
    revenue = SimpleNamespace(
        checkin_date=date(2026, 4, 8),
        date=date(2026, 4, 10),
        gross_amount=Decimal("1200.00"),
        net_amount=Decimal("1000.00"),
        cleaning_fee=Decimal("150.00"),
        platform_fee=Decimal("50.00"),
    )

    updated = await service.update(
        revenue,
        {
            "net_amount": 1100.0,
            "cleaning_fee": 120.0,
            "platform_fee": 80.0,
        },
    )

    assert float(updated.gross_amount) == 1300.0
    assert session.commit_calls == 1
    assert session.refresh_calls == 1


@pytest.mark.asyncio
async def test_create_revenue_preserves_pending_amount():
    session = FakeAsyncSession()
    service = RevenueService(session)

    revenue = await service.create(
        uuid.uuid4(),
        {
            "property_id": uuid.uuid4(),
            "year_month": "2026-04",
            "date": date(2026, 4, 10),
            "checkin_date": date(2026, 4, 8),
            "guest_name": "Hospede Teste",
            "nights": 3,
            "net_amount": 1000.0,
            "cleaning_fee": 150.0,
            "platform_fee": 50.0,
            "pending_amount": 275.5,
        },
    )

    assert float(revenue.pending_amount) == 275.5


@pytest.mark.asyncio
async def test_update_revenue_updates_pending_amount():
    session = FakeAsyncSession()
    service = RevenueService(session)
    revenue = SimpleNamespace(
        checkin_date=date(2026, 4, 8),
        date=date(2026, 4, 10),
        gross_amount=Decimal("1200.00"),
        net_amount=Decimal("1000.00"),
        cleaning_fee=Decimal("150.00"),
        platform_fee=Decimal("50.00"),
        pending_amount=Decimal("0.00"),
    )

    updated = await service.update(
        revenue,
        {
            "pending_amount": 320.0,
        },
    )

    assert float(updated.pending_amount) == 320.0


@pytest.mark.asyncio
async def test_create_revenue_derives_pending_from_notes_text():
    session = FakeAsyncSession()
    service = RevenueService(session)

    revenue = await service.create(
        uuid.uuid4(),
        {
            "property_id": uuid.uuid4(),
            "year_month": "2026-04",
            "date": date(2026, 4, 10),
            "checkin_date": date(2026, 4, 8),
            "guest_name": "Hospede Teste",
            "nights": 3,
            "net_amount": 1000.0,
            "cleaning_fee": 150.0,
            "platform_fee": 50.0,
            "notes": "Relatorio de pagamento: pendente R$ 2.610,03",
        },
    )

    assert float(revenue.pending_amount) == 2610.03


@pytest.mark.asyncio
async def test_create_revenue_marks_pending_when_status_is_pending():
    session = FakeAsyncSession()
    service = RevenueService(session)

    revenue = await service.create(
        uuid.uuid4(),
        {
            "property_id": uuid.uuid4(),
            "year_month": "2026-04",
            "date": date(2026, 4, 10),
            "checkin_date": date(2026, 4, 8),
            "guest_name": "Hospede Teste",
            "nights": 3,
            "net_amount": 1350.0,
            "cleaning_fee": 150.0,
            "platform_fee": 50.0,
            "payment_status": "pendente",
        },
    )

    assert float(revenue.pending_amount) == 1350.0


@pytest.mark.asyncio
async def test_get_calendar_reservations_filters_by_stay_overlap():
    engine = create_async_engine("sqlite+aiosqlite:///./test_revenue_calendar.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db_session:
        user = User(
            id=uuid.uuid4(),
            email="calendar@test.com",
            hashed_password="hashed",
            full_name="Calendar Test",
            is_active=True,
            is_superuser=False,
        )
        property_item = Property(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Calendario Teste",
            property_value=Decimal("300000.00"),
            monthly_depreciation_percent=Decimal("1.00"),
            is_active=True,
        )
        overlapping_revenue = RentalRevenue(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=property_item.id,
            year_month="2026-05",
            date=date(2026, 4, 10),
            checkin_date=date(2026, 4, 9),
            checkout_date=date(2026, 4, 12),
            guest_name="Hospede Dentro",
            nights=3,
            gross_amount=Decimal("800.00"),
            cleaning_fee=Decimal("80.00"),
            platform_fee=Decimal("20.00"),
            net_amount=Decimal("700.00"),
        )
        outside_revenue = RentalRevenue(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=property_item.id,
            year_month="2026-05",
            date=date(2026, 4, 20),
            checkin_date=date(2026, 4, 20),
            checkout_date=date(2026, 4, 22),
            guest_name="Hospede Fora",
            nights=2,
            gross_amount=Decimal("500.00"),
            cleaning_fee=Decimal("50.00"),
            platform_fee=Decimal("10.00"),
            net_amount=Decimal("440.00"),
        )

        db_session.add_all([user, property_item, overlapping_revenue, outside_revenue])
        await db_session.commit()

        service = RevenueService(db_session)
        reservations = await service.get_calendar_reservations(
            user.id,
            property_item.id,
            date(2026, 4, 1),
            date(2026, 4, 15),
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    assert [reservation.guest_name for reservation in reservations] == ["Hospede Dentro"]
