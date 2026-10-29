import uuid
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.keycloak import (
    KeycloakTokenError,
    decode_keycloak_token_async,
    is_keycloak_access_token,
)
from app.database import get_db
from app.models import User
from app.services.auth_service import AuthService
from app.utils.security import decode_token


security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)

_NOT_REGISTERED = "Usuário não cadastrado"


async def _resolve_keycloak_user(token: str, db: AsyncSession) -> User:
    try:
        payload = await decode_keycloak_token_async(token)
    except KeycloakTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    email = payload.get("email")
    user: User | None = None

    if isinstance(sub, str) and sub:
        result = await db.execute(select(User).where(User.keycloak_sub == sub))
        user = result.scalar_one_or_none()

    if user is None and isinstance(email, str) and email.strip():
        result = await db.execute(
            select(User).where(func.lower(User.email) == email.strip().lower())
        )
        user = result.scalar_one_or_none()
        if user is not None and isinstance(sub, str) and sub:
            if user.keycloak_sub != sub:
                user.keycloak_sub = sub
                await db.commit()
                await db.refresh(user)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_NOT_REGISTERED,
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    # Client roles do token são apenas informativas; permissões locais mandam.
    return user


async def _resolve_legacy_user(token: str, db: AsyncSession) -> User:
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    if api_key:
        result = await db.execute(
            select(User).where(User.api_token == api_key, User.is_active.is_(True))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if is_keycloak_access_token(token):
        return await _resolve_keycloak_user(token, db)

    if not settings.auth_legacy_password_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await _resolve_legacy_user(token, db)


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
