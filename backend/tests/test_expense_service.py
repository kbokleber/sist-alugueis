from datetime import date
from types import SimpleNamespace
import uuid

import pytest

from app.models.property_expense import ExpenseStatus
from app.services.expense_service import ExpenseService


class FakeAsyncSession:
    def __init__(self):
        self.commit_calls = 0
        self.refresh_calls = 0

    async def commit(self):
        self.commit_calls += 1

    async def refresh(self, _instance):
        self.refresh_calls += 1


def build_base_payload():
    return {
        "property_id": uuid.uuid4(),
        "category_id": uuid.uuid4(),
        "name": "Internet",
        "amount": 199.9,
        "is_reserve": False,
        "notes": "Conta fixa",
    }


def test_build_create_payloads_generates_monthly_pending_expenses():
    payloads = ExpenseService.build_create_payloads(
        {
            **build_base_payload(),
            "is_recurring": True,
            "recurrence_type": "MONTHLY",
            "recurrence_start_date": date(2026, 1, 31),
            "recurrence_end_date": date(2026, 3, 31),
        }
    )

    assert [item["year_month"] for item in payloads] == ["2026-01", "2026-02", "2026-03"]
    assert [item["due_date"] for item in payloads] == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
    ]
    assert all(item["name"] == "[Recorrente] Internet" for item in payloads)
    assert all(item["status"] == ExpenseStatus.PENDING for item in payloads)
    assert all(item["paid_date"] is None for item in payloads)


def test_build_create_payloads_generates_annual_pending_expenses():
    payloads = ExpenseService.build_create_payloads(
        {
            **build_base_payload(),
            "is_recurring": True,
            "recurrence_type": "ANNUAL",
            "recurrence_start_date": date(2024, 2, 29),
            "recurrence_end_date": date(2026, 2, 28),
        }
    )

    assert [item["due_date"] for item in payloads] == [
        date(2024, 2, 29),
        date(2025, 2, 28),
        date(2026, 2, 28),
    ]
    assert [item["year_month"] for item in payloads] == ["2024-02", "2025-02", "2026-02"]


def test_build_create_payloads_rejects_invalid_recurrence_range():
    with pytest.raises(ValueError):
        ExpenseService.build_create_payloads(
            {
                **build_base_payload(),
                "is_recurring": True,
                "recurrence_type": "MONTHLY",
                "recurrence_start_date": date(2026, 5, 10),
                "recurrence_end_date": date(2026, 4, 10),
            }
        )


def test_build_create_payloads_accepts_optional_name_for_non_recurring():
    payloads = ExpenseService.build_create_payloads(
        {
            **build_base_payload(),
            "name": None,
            "year_month": "2026-04",
            "due_date": date(2026, 4, 5),
        }
    )

    assert payloads[0]["name"] == "Despesa"


def test_build_create_payloads_accepts_optional_name_for_recurring():
    payloads = ExpenseService.build_create_payloads(
        {
            **build_base_payload(),
            "name": None,
            "is_recurring": True,
            "recurrence_type": "MONTHLY",
            "recurrence_start_date": date(2026, 4, 5),
            "recurrence_end_date": date(2026, 5, 5),
        }
    )

    assert [item["name"] for item in payloads] == ["[Recorrente]", "[Recorrente]"]


@pytest.mark.asyncio
async def test_set_status_to_paid_defaults_paid_date_and_can_reopen_to_pending():
    session = FakeAsyncSession()
    service = ExpenseService(session)
    expense = SimpleNamespace(status=ExpenseStatus.PENDING, paid_date=None)

    paid_expense = await service.set_status(expense, ExpenseStatus.PAID)

    assert paid_expense.status == ExpenseStatus.PAID
    assert paid_expense.paid_date == date.today()

    reopened_expense = await service.set_status(expense, ExpenseStatus.PENDING)

    assert reopened_expense.status == ExpenseStatus.PENDING
    assert reopened_expense.paid_date is None
    assert session.commit_calls == 2
    assert session.refresh_calls == 2
