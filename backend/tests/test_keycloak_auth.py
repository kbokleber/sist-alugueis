"""Testes de autenticação Keycloak + legado + X-API-Token."""
from __future__ import annotations

import time
import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core import keycloak as keycloak_mod
from app.core.keycloak import (
    KeycloakTokenError,
    clear_jwks_cache,
    decode_keycloak_token,
    is_keycloak_access_token,
)
from app.database import Base, get_db
from app.main import app
from app.models import User
from app.utils.security import create_access_token, hash_password


ISSUER = "https://auth.kbosolucoes.com.br/realms/familia"
AUDIENCE = "alugueis"
CLIENT_ID = "alugueis"


@pytest.fixture(scope="module")
def rsa_keys():
    import base64

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    numbers = private_key.public_key().public_numbers()

    def _b64url_uint(val: int) -> str:
        raw = val.to_bytes((val.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    jwk = {
        "kty": "RSA",
        "kid": "test-kid",
        "use": "sig",
        "alg": "RS256",
        "n": _b64url_uint(numbers.n),
        "e": _b64url_uint(numbers.e),
    }
    return {"private_pem": private_pem, "jwks": {"keys": [jwk]}, "kid": "test-kid"}


def _make_token(private_pem: bytes, kid: str, claims: dict) -> str:
    headers = {"kid": kid, "alg": "RS256"}
    return jwt.encode(claims, private_pem, algorithm="RS256", headers=headers)


@pytest.fixture(autouse=True)
def _keycloak_settings(rsa_keys):
    clear_jwks_cache()
    with (
        patch.object(settings, "keycloak_url", "https://auth.kbosolucoes.com.br"),
        patch.object(settings, "keycloak_realm", "familia"),
        patch.object(settings, "keycloak_issuer", ISSUER),
        patch.object(settings, "keycloak_client_id", CLIENT_ID),
        patch.object(settings, "keycloak_audience", AUDIENCE),
        patch.object(settings, "auth_legacy_password_enabled", True),
        patch.object(keycloak_mod, "get_jwks", return_value=rsa_keys["jwks"]),
    ):
        yield
    clear_jwks_cache()


@pytest_asyncio.fixture
async def db_env():
    """Session + usuário seed."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        user = User(
            id=uuid.uuid4(),
            email="kbosolucoes@gmail.com",
            hashed_password=hash_password("secret123"),
            full_name="Kleber",
            is_active=True,
            is_superuser=True,
            api_token="static-api-token-xyz",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        async def override_db():
            yield session

        app.dependency_overrides[get_db] = override_db
        try:
            yield session, user
        finally:
            app.dependency_overrides.pop(get_db, None)

    await engine.dispose()


def test_is_keycloak_token_by_issuer(rsa_keys):
    token = _make_token(
        rsa_keys["private_pem"],
        rsa_keys["kid"],
        {
            "iss": ISSUER,
            "sub": "kc-sub-1",
            "aud": AUDIENCE,
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        },
    )
    assert is_keycloak_access_token(token) is True

    legacy = create_access_token({"sub": str(uuid.uuid4()), "email": "a@b.com"})
    assert is_keycloak_access_token(legacy) is False


def test_decode_rejects_wrong_audience(rsa_keys):
    token = _make_token(
        rsa_keys["private_pem"],
        rsa_keys["kid"],
        {
            "iss": ISSUER,
            "sub": "kc-sub-1",
            "aud": "outro-client",
            "azp": "outro-client",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        },
    )
    with pytest.raises(KeycloakTokenError):
        decode_keycloak_token(token)


def test_decode_accepts_azp_when_aud_missing(rsa_keys):
    token = _make_token(
        rsa_keys["private_pem"],
        rsa_keys["kid"],
        {
            "iss": ISSUER,
            "sub": "kc-sub-1",
            "azp": CLIENT_ID,
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        },
    )
    payload = decode_keycloak_token(token)
    assert payload["sub"] == "kc-sub-1"


def test_decode_rejects_wrong_issuer(rsa_keys):
    token = _make_token(
        rsa_keys["private_pem"],
        rsa_keys["kid"],
        {
            "iss": "https://auth.kbosolucoes.com.br/realms/outro",
            "sub": "kc-sub-1",
            "aud": AUDIENCE,
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        },
    )
    # is_keycloak_access_token false; decode still fails on iss
    assert is_keycloak_access_token(token) is False
    with pytest.raises(KeycloakTokenError):
        decode_keycloak_token(token)


def test_decode_rejects_expired(rsa_keys):
    token = _make_token(
        rsa_keys["private_pem"],
        rsa_keys["kid"],
        {
            "iss": ISSUER,
            "sub": "kc-sub-1",
            "aud": AUDIENCE,
            "exp": int(time.time()) - 120,
            "iat": int(time.time()) - 200,
        },
    )
    with pytest.raises(KeycloakTokenError):
        decode_keycloak_token(token)


@pytest.mark.asyncio
async def test_keycloak_maps_by_email_case_insensitive(db_env, rsa_keys):
    session, user = db_env
    token = _make_token(
        rsa_keys["private_pem"],
        rsa_keys["kid"],
        {
            "iss": ISSUER,
            "sub": "kc-sub-new",
            "email": "KBOSolucoes@Gmail.COM",
            "aud": AUDIENCE,
            "azp": CLIENT_ID,
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "resource_access": {CLIENT_ID: {"roles": ["admin"]}},
        },
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == user.email

    await session.refresh(user)
    assert user.keycloak_sub == "kc-sub-new"


@pytest.mark.asyncio
async def test_keycloak_blocks_unknown_user(db_env, rsa_keys):
    _session, _user = db_env
    token = _make_token(
        rsa_keys["private_pem"],
        rsa_keys["kid"],
        {
            "iss": ISSUER,
            "sub": "unknown-sub",
            "email": "naoexiste@kbosolucoes.com.br",
            "aud": AUDIENCE,
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        },
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 403
    assert response.json()["detail"] == "Usuário não cadastrado"


@pytest.mark.asyncio
async def test_api_token_header(db_env):
    _session, _user = db_env
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ok = await client.get(
            "/api/v1/auth/me",
            headers={"X-API-Token": "static-api-token-xyz"},
        )
        bad = await client.get(
            "/api/v1/auth/me",
            headers={"X-API-Token": "wrong"},
        )
    assert ok.status_code == 200
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_legacy_login_enabled(db_env):
    _session, user = db_env
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "secret123"},
        )
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]


@pytest.mark.asyncio
async def test_legacy_login_disabled(db_env):
    _session, user = db_env
    with patch.object(settings, "auth_legacy_password_enabled", False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": user.email, "password": "secret123"},
            )
            config = await client.get("/api/v1/auth/config")
    assert response.status_code == 403
    assert config.status_code == 200
    assert config.json()["data"]["legacy_enabled"] is False
    assert config.json()["data"]["realm"] == "familia"
