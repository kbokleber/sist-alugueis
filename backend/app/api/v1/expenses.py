import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpensePayPatch,
    ExpenseResponse,
    ExpenseByCategory,
    ResponseWrapper,
)
from app.services.expense_service import ExpenseService
from app.services.audit_service import AuditService
from app.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=ResponseWrapper[list[ExpenseResponse]])
async def list_expenses(
    property_id: uuid.UUID | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    year_month: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    skip = (page - 1) * per_page
    expenses, total = await service.get_all(
        user_id=current_user.id,
        property_id=property_id,
        category_id=category_id,
        year_month=year_month,
        status=status_filter,
        skip=skip,
        limit=per_page,
    )
    total_pages = (total + per_page - 1) // per_page
    return ResponseWrapper(
        data=expenses,
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )


@router.post("", response_model=ResponseWrapper[ExpenseResponse], status_code=status.HTTP_201_CREATED)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    expense = await service.create(current_user.id, data.model_dump())

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CREATE",
        entity_type="expense",
        entity_id=expense.id,
        new_values=data.model_dump(),
    )

    return ResponseWrapper(data=expense, message="Expense created successfully")


@router.get("/by-category", response_model=ResponseWrapper[list[ExpenseByCategory]])
async def get_expenses_by_category(
    year_month: str | None = Query(None),
    property_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    result = await service.get_by_category(current_user.id, year_month, property_id)
    return ResponseWrapper(data=result)


@router.get("/{expense_id}", response_model=ResponseWrapper[ExpenseResponse])
async def get_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    expense = await service.get_by_id(expense_id, current_user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return ResponseWrapper(data=expense)


@router.put("/{expense_id}", response_model=ResponseWrapper[ExpenseResponse])
async def update_expense(
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    expense = await service.get_by_id(expense_id, current_user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Capture old values before update
    old_values = {
        "property_id": str(expense.property_id),
        "category_id": str(expense.category_id) if expense.category_id else None,
        "amount": float(expense.amount),
        "due_date": expense.due_date.isoformat() if expense.due_date else None,
        "description": expense.description,
        "year_month": expense.year_month,
        "status": expense.status.value if hasattr(expense.status, 'value') else str(expense.status),
        "invoice_number": expense.invoice_number,
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

    return ResponseWrapper(data=updated)


@router.patch("/{expense_id}/pay", response_model=ResponseWrapper[ExpenseResponse])
async def mark_expense_paid(
    expense_id: uuid.UUID,
    data: ExpensePayPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    expense = await service.get_by_id(expense_id, current_user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Capture old values
    old_values = {
        "status": expense.status.value if hasattr(expense.status, 'value') else str(expense.status),
        "paid_date": expense.paid_date.isoformat() if expense.paid_date else None,
    }

    updated = await service.mark_paid(expense, data.paid_date)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="expense",
        entity_id=expense_id,
        old_values=old_values,
        new_values={"status": "PAID", "paid_date": data.paid_date.isoformat() if data.paid_date else None},
    )

    return ResponseWrapper(data=updated, message="Expense marked as paid")


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    expense = await service.get_by_id(expense_id, current_user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Capture old values before delete
    old_values = {
        "property_id": str(expense.property_id),
        "category_id": str(expense.category_id) if expense.category_id else None,
        "amount": float(expense.amount),
        "due_date": expense.due_date.isoformat() if expense.due_date else None,
        "description": expense.description,
        "year_month": expense.year_month,
        "status": expense.status.value if hasattr(expense.status, 'value') else str(expense.status),
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
