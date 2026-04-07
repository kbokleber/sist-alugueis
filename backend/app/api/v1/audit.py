import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import ResponseWrapper, AuditLogResponse
from app.services.audit_service import AuditService
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(prefix="/audit", tags=["audit"])


def serialize_audit_log(log) -> AuditLogResponse:
    return AuditLogResponse.model_validate(log)


@router.get("", response_model=ResponseWrapper[list[AuditLogResponse]])
async def list_audit_logs(
    entity_type: str | None = Query(None),
    entity_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AuditService(db)
    skip = (page - 1) * per_page
    logs, total = await service.get_all(
        user_id=current_user.id if not current_user.is_superuser else None,
        entity_type=entity_type,
        entity_id=entity_id,
        skip=skip,
        limit=per_page,
    )
    total_pages = (total + per_page - 1) // per_page
    return ResponseWrapper(
        data=[serialize_audit_log(log) for log in logs],
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    )


@router.get("/{entity_type}/{entity_id}", response_model=ResponseWrapper[list[AuditLogResponse]])
async def get_entity_history(
    entity_type: str,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AuditService(db)
    logs = await service.get_entity_history(entity_type, entity_id)
    return ResponseWrapper(data=[serialize_audit_log(log) for log in logs])
