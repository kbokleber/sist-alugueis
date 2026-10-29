"""Validação de access token do Keycloak (realm familia) via JWKS."""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional
from urllib.parse import quote

import httpx
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.config import settings

logger = logging.getLogger(__name__)

_jwks_lock = threading.Lock()
_jwks_cache: dict[str, Any] = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL_SECONDS = 600  # ~10 min
_CLOCK_SKEW_SECONDS = 30


class KeycloakTokenError(Exception):
    """Token Bearer não é um JWT válido deste realm."""


def keycloak_issuer() -> str:
    if settings.keycloak_issuer:
        return settings.keycloak_issuer.rstrip("/")
    realm = quote(settings.keycloak_realm, safe="")
    return f"{settings.keycloak_url.rstrip('/')}/realms/{realm}"


def keycloak_enabled() -> bool:
    return bool(settings.keycloak_url and settings.keycloak_realm and settings.keycloak_client_id)


def _jwks_url() -> str:
    return f"{keycloak_issuer()}/protocol/openid-connect/certs"


def get_jwks(*, force: bool = False) -> dict:
    now = time.time()
    with _jwks_lock:
        cached = _jwks_cache["keys"]
        if (
            not force
            and cached is not None
            and now - float(_jwks_cache["fetched_at"]) < _JWKS_TTL_SECONDS
        ):
            return cached

    # Timeout curto: se o Keycloak estiver lento, falha em vez de travar o worker.
    with httpx.Client(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
        response = client.get(_jwks_url())
        response.raise_for_status()
        data = response.json()

    with _jwks_lock:
        _jwks_cache["keys"] = data
        _jwks_cache["fetched_at"] = time.time()
    return data


async def get_jwks_async(*, force: bool = False) -> dict:
    """JWKS fora do event loop (httpx sync não bloqueia o asyncio)."""
    import asyncio

    return await asyncio.to_thread(get_jwks, force=force)


async def decode_keycloak_token_async(token: str) -> dict:
    """Versão async: busca JWKS em thread e valida o JWT."""
    issuer = keycloak_issuer()
    last_error: Optional[Exception] = None

    for force in (False, True):
        try:
            jwks = await get_jwks_async(force=force)
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                issuer=issuer,
                options={
                    "verify_aud": False,
                    "verify_exp": False,
                    "verify_iss": True,
                },
            )
            if not _exp_ok(payload):
                raise ExpiredSignatureError("Token expirado")
            if not _audience_ok(payload):
                raise KeycloakTokenError("Audience inválida")
            return payload
        except KeycloakTokenError:
            raise
        except ExpiredSignatureError as exc:
            raise KeycloakTokenError("Token expirado") from exc
        except JWTError as exc:
            last_error = exc
            logger.info("Token Keycloak rejeitado (refresh_jwks=%s): %s", force, exc)
        except httpx.HTTPError as exc:
            logger.exception("Falha ao buscar JWKS do Keycloak")
            raise KeycloakTokenError("Não foi possível validar o token") from exc

    raise KeycloakTokenError("Token Keycloak inválido") from last_error


def clear_jwks_cache() -> None:
    with _jwks_lock:
        _jwks_cache["keys"] = None
        _jwks_cache["fetched_at"] = 0.0


def _unverified_claims(token: str) -> Optional[dict]:
    try:
        claims = jwt.get_unverified_claims(token)
    except JWTError:
        return None
    return claims if isinstance(claims, dict) else None


def is_keycloak_access_token(token: str) -> bool:
    """True quando o `iss` do token é o deste realm (sem validar assinatura)."""
    if not keycloak_enabled():
        return False
    claims = _unverified_claims(token)
    if not claims:
        return False
    return claims.get("iss") == keycloak_issuer()


def _audience_ok(payload: dict) -> bool:
    expected = settings.keycloak_audience or settings.keycloak_client_id
    aud = payload.get("aud")
    if isinstance(aud, str) and aud == expected:
        return True
    if isinstance(aud, list) and expected in aud:
        return True
    azp = payload.get("azp")
    if isinstance(azp, str) and azp == settings.keycloak_client_id:
        return True
    return False


def _exp_ok(payload: dict) -> bool:
    exp = payload.get("exp")
    if exp is None:
        return False
    return float(exp) + _CLOCK_SKEW_SECONDS >= time.time()


def decode_keycloak_token(token: str) -> dict:
    """Valida assinatura RS256 (JWKS), iss, aud/azp e exp. Recarrega JWKS se kid desconhecido."""
    issuer = keycloak_issuer()
    last_error: Optional[Exception] = None

    for force in (False, True):
        try:
            payload = jwt.decode(
                token,
                get_jwks(force=force),
                algorithms=["RS256"],
                issuer=issuer,
                options={
                    "verify_aud": False,
                    "verify_exp": False,
                    "verify_iss": True,
                },
            )
            if not _exp_ok(payload):
                raise ExpiredSignatureError("Token expirado")
            if not _audience_ok(payload):
                raise KeycloakTokenError("Audience inválida")
            return payload
        except KeycloakTokenError:
            raise
        except ExpiredSignatureError as exc:
            raise KeycloakTokenError("Token expirado") from exc
        except JWTError as exc:
            last_error = exc
            logger.info("Token Keycloak rejeitado (refresh_jwks=%s): %s", force, exc)
        except httpx.HTTPError as exc:
            logger.exception("Falha ao buscar JWKS do Keycloak")
            raise KeycloakTokenError("Não foi possível validar o token") from exc

    raise KeycloakTokenError("Token Keycloak inválido") from last_error


def client_roles(payload: dict) -> set[str]:
    """Lê resource_access.<client>.roles (informativo; permissões locais mandam)."""
    resource_access = payload.get("resource_access") or {}
    client = resource_access.get(settings.keycloak_client_id) or {}
    roles = client.get("roles") or []
    return {str(role) for role in roles}
