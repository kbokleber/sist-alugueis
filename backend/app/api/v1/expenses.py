import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpensePayPatch,
    ExpenseStatusPatch,
    ExpenseResponse,
    ExpenseByCategory,
    ResponseWrapper,
)
from app.services.expense_service import ExpenseService
from app.services.audit_service import AuditService
from app.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix="/expenses", tags=["expenses"])


def serialize_expense(expense) -> ExpenseResponse:
    is_recurring = expense.name.startswith("[Recorrente]")
    return ExpenseResponse.model_validate(
        {
            "id": expense.id,
            "user_id": expense.user_id,
            "is_recurring": is_recurring,
            "property_id": expense.property_id,
            "property_code": expense.property.code if expense.property else None,
            "property_name": expense.property.name if expense.property else None,
            "category_id": expense.category_id,
            "category_name": expense.category.name if expense.category else None,
            "year_month": expense.year_month,
            "name": expense.name,
            "amount": float(expense.amount),
            "is_reserve": expense.is_reserve,
            "due_date": expense.due_date,
            "paid_date": expense.paid_date,
            "status": expense.status,
            "source": expense.source,
            "notes": expense.notes,
            "created_at": expense.created_at,
            "updated_at": expense.updated_at,
        }
    )


@router.get("", response_model=ResponseWrapper[list[ExpenseResponse]])
async def list_expenses(
    property_id: uuid.UUID | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    year_month: str | None = Query(None),
    start_month: str | None = Query(None),
    end_month: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    skip = (page - 1) * per_page
    expenses, total = await service.get_all(
        user_id=scope_user_id,
        property_id=property_id,
        category_id=category_id,
        year_month=year_month,
        start_month=start_month,
        end_month=end_month,
        status=status_filter,
        skip=skip,
        limit=per_page,
    )
    total_pages = (total + per_page - 1) // per_page
    return ResponseWrapper(
        data=[serialize_expense(expense) for expense in expenses],
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )


@router.post("", response_model=ResponseWrapper[list[ExpenseResponse]], status_code=status.HTTP_201_CREATED)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    try:
        expenses = await service.create(current_user.id, data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Audit log
    audit_service = AuditService(db)
    for expense in expenses:
        await audit_service.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="expense",
            entity_id=expense.id,
            new_values={
                **data.model_dump(exclude={"is_recurring", "recurrence_type", "recurrence_start_date", "recurrence_end_date"}),
                "year_month": expense.year_month,
                "due_date": expense.due_date,
                "status": expense.status.value if hasattr(expense.status, "value") else str(expense.status),
                "paid_date": expense.paid_date,
            },
        )

    created_count = len(expenses)
    message = "Expense created successfully" if created_count == 1 else f"{created_count} expenses created successfully"
    return ResponseWrapper(
        data=[serialize_expense(expense) for expense in expenses],
        message=message,
    )


@router.get("/by-category", response_model=ResponseWrapper[list[ExpenseByCategory]])
async def get_expenses_by_category(
    year_month: str | None = Query(None),
    property_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    result = await service.get_by_category(scope_user_id, year_month, property_id)
    return ResponseWrapper(data=result)


@router.get("/{expense_id}", response_model=ResponseWrapper[ExpenseResponse])
async def get_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    expense = await service.get_by_id(expense_id, scope_user_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return ResponseWrapper(data=serialize_expense(expense))


@router.put("/{expense_id}", response_model=ResponseWrapper[ExpenseResponse])
async def update_expense(
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    expense = await service.get_by_id(expense_id, scope_user_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Capture old values before update
    old_values = {
        "property_id": str(expense.property_id),
        "category_id": str(expense.category_id) if expense.category_id else None,
        "year_month": expense.year_month,
        "name": expense.name,
        "amount": float(expense.amount),
        "is_reserve": expense.is_reserve,
        "due_date": expense.due_date.isoformat() if expense.due_date else None,
        "paid_date": expense.paid_date.isoformat() if expense.paid_date else None,
        "status": expense.status.value if hasattr(expense.status, 'value') else str(expense.status),
        "notes": expense.notes,
    }

    updated = await service.update(expense, data.model_dump(exclude_unset=True))

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="expense",
        entity_id=expense_id,
        old_values=old_values,
        new_values=data.model_dump(exclude_unset=True),
    )

    return ResponseWrapper(data=serialize_expense(updated))


@router.patch("/{expense_id}/pay", response_model=ResponseWrapper[ExpenseResponse])
async def mark_expense_paid(
    expense_id: uuid.UUID,
    data: ExpensePayPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    expense = await service.get_by_id(expense_id, scope_user_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Capture old values
    old_values = {
        "status": expense.status.value if hasattr(expense.status, 'value') else str(expense.status),
        "paid_date": expense.paid_date.isoformat() if expense.paid_date else None,
    }

    updated = await service.set_status(expense, data.status, data.paid_date)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="expense",
        entity_id=expense_id,
        old_values=old_values,
        new_values={
            "status": updated.status.value if hasattr(updated.status, "value") else str(updated.status),
            "paid_date": updated.paid_date.isoformat() if updated.paid_date else None,
        },
    )

    return ResponseWrapper(data=serialize_expense(updated), message="Expense marked as paid")


@router.patch("/{expense_id}/status", response_model=ResponseWrapper[ExpenseResponse])
async def update_expense_status(
    expense_id: uuid.UUID,
    data: ExpenseStatusPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    expense = await service.get_by_id(expense_id, scope_user_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    old_values = {
        "status": expense.status.value if hasattr(expense.status, "value") else str(expense.status),
        "paid_date": expense.paid_date.isoformat() if expense.paid_date else None,
    }

    updated = await service.set_status(expense, data.status, data.paid_date)

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="expense",
        entity_id=expense_id,
        old_values=old_values,
        new_values={
            "status": updated.status.value if hasattr(updated.status, "value") else str(updated.status),
            "paid_date": updated.paid_date.isoformat() if updated.paid_date else None,
        },
    )

    return ResponseWrapper(data=serialize_expense(updated), message="Expense status updated successfully")


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    expense = await service.get_by_id(expense_id, scope_user_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Capture old values before delete
    old_values = {
        "property_id": str(expense.property_id),
        "category_id": str(expense.category_id) if expense.category_id else None,
        "year_month": expense.year_month,
        "name": expense.name,
        "amount": float(expense.amount),
        "is_reserve": expense.is_reserve,
        "due_date": expense.due_date.isoformat() if expense.due_date else None,
        "paid_date": expense.paid_date.isoformat() if expense.paid_date else None,
        "status": expense.status.value if hasattr(expense.status, 'value') else str(expense.status),
        "notes": expense.notes,
    }

    await service.delete(expense)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="DELETE",
        entity_type="expense",
        entity_id=expense_id,
        old_values=old_values,
    )

    return {"message": "Expense deleted successfully"}
