import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    ChecklistCreate,
    ChecklistItemsUpdate,
    ChecklistResponse,
    ChecklistSummary,
    ResponseWrapper,
)
from app.services.audit_service import AuditService
from app.services.checklist_service import ChecklistService

router = APIRouter(tags=["checklists"])


def _performed_by_name(checklist) -> str | None:
    performer = checklist.__dict__.get("performed_by")
    if performer is None:
        return None
    return getattr(performer, "full_name", None) or getattr(performer, "email", None)


def serialize_checklist(checklist) -> ChecklistResponse:
    payload = ChecklistResponse.model_validate(checklist).model_dump()
    payload["performed_by_name"] = _performed_by_name(checklist)
    return ChecklistResponse.model_validate(payload)


def serialize_checklist_summary(checklist) -> ChecklistSummary:
    payload = ChecklistSummary.model_validate(checklist).model_dump()
    payload["performed_by_name"] = _performed_by_name(checklist)
    return ChecklistSummary.model_validate(payload)


@router.get(
    "/checklists",
    response_model=ResponseWrapper[list[ChecklistSummary]],
)
async def list_checklists(
    property_id: uuid.UUID | None = Query(None),
    has_incidents: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChecklistService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    checklists = await service.list_all(
        user_id=scope_user_id,
        property_id=property_id,
        has_incidents=has_incidents,
    )
    return ResponseWrapper(data=[serialize_checklist_summary(c) for c in checklists])


@router.get(
    "/revenues/{revenue_id}/checklists",
    response_model=ResponseWrapper[list[ChecklistResponse]],
)
async def list_revenue_checklists(
    revenue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChecklistService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    revenue = await service.get_revenue(revenue_id, scope_user_id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Receita/estadia não encontrada")
    checklists = await service.list_for_revenue(revenue_id, scope_user_id)
    return ResponseWrapper(data=[serialize_checklist(c) for c in checklists])


@router.post(
    "/revenues/{revenue_id}/checklists",
    response_model=ResponseWrapper[ChecklistResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_checklist(
    revenue_id: uuid.UUID,
    data: ChecklistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChecklistService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    revenue = await service.get_revenue(revenue_id, scope_user_id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Receita/estadia não encontrada")

    try:
        checklist = await service.create_from_inventory(
            revenue,
            data.checklist_type,
            performed_by_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="CREATE",
        entity_type="stay_checklist",
        entity_id=checklist.id,
        new_values={
            "rental_revenue_id": str(revenue_id),
            "checklist_type": data.checklist_type.value,
        },
    )
    return ResponseWrapper(data=serialize_checklist(checklist), message="Checklist criado")


@router.get(
    "/checklists/{checklist_id}",
    response_model=ResponseWrapper[ChecklistResponse],
)
async def get_checklist(
    checklist_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChecklistService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    checklist = await service.get_by_id(checklist_id, scope_user_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist não encontrado")
    return ResponseWrapper(data=serialize_checklist(checklist))


@router.put(
    "/checklists/{checklist_id}/items",
    response_model=ResponseWrapper[ChecklistResponse],
)
async def update_checklist_items(
    checklist_id: uuid.UUID,
    data: ChecklistItemsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChecklistService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    checklist = await service.get_by_id(checklist_id, scope_user_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist não encontrado")

    try:
        updated = await service.update_items(
            checklist,
            [item.model_dump(exclude_unset=True) for item in data.items],
            general_notes=data.general_notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="stay_checklist",
        entity_id=checklist_id,
        new_values={"items_updated": len(data.items)},
    )
    return ResponseWrapper(data=serialize_checklist(updated))


@router.post(
    "/checklists/{checklist_id}/complete",
    response_model=ResponseWrapper[ChecklistResponse],
)
async def complete_checklist(
    checklist_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChecklistService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    checklist = await service.get_by_id(checklist_id, scope_user_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist não encontrado")

    try:
        completed = await service.complete(checklist, performed_by_user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="stay_checklist",
        entity_id=checklist_id,
        new_values={
            "status": "completed",
            "has_incidents": completed.has_incidents,
            "performed_by_name": current_user.full_name,
        },
    )
    return ResponseWrapper(data=serialize_checklist(completed), message="Checklist concluído")


@router.post(
    "/checklists/{checklist_id}/reopen",
    response_model=ResponseWrapper[ChecklistResponse],
)
async def reopen_checklist(
    checklist_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if getattr(current_user, "app_profile", "full") == "checklist":
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem reabrir checklist concluído",
        )

    service = ChecklistService(db)
    scope_user_id = None if current_user.is_superuser else current_user.id
    checklist = await service.get_by_id(checklist_id, scope_user_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist não encontrado")

    try:
        reopened = await service.reopen(checklist)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="UPDATE",
        entity_type="stay_checklist",
        entity_id=checklist_id,
        new_values={"status": "draft", "reopened": True},
    )
    return ResponseWrapper(
        data=serialize_checklist(reopened), message="Checklist reaberto para refazer"
    )
