from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import uuid

import pytest

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
