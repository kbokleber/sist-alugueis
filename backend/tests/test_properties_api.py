import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.dependencies import get_current_user
from app.main import app
from app.models import Property, User


@pytest.mark.asyncio
async def test_property_update_persists_financial_fields():
    engine = create_async_engine("sqlite+aiosqlite:///./test_properties_api.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db_session:
        user = User(
            id=uuid.uuid4(),
            email="property-api@test.com",
            hashed_password="hashed",
            full_name="Property API Test",
            is_active=True,
            is_superuser=False,
        )
        prop = Property(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Imóvel API",
            property_value=Decimal("400000.00"),
            monthly_depreciation_percent=Decimal("1.00"),
            default_cleaning_fee=Decimal("170.00"),
            platform_fee_percent=Decimal("15.00"),
            is_active=True,
        )
        db_session.add_all([user, prop])
        await db_session.commit()

        async def override_current_user():
            return user

        async def override_db():
            yield db_session

        app.dependency_overrides[get_current_user] = override_current_user
        app.dependency_overrides[get_db] = override_db

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                list_response = await client.get(
                    "/api/v1/properties",
                    headers={"Authorization": "Bearer test-token"},
                )
                assert list_response.status_code == 200
                listed = list_response.json()["data"][0]
                assert listed["default_cleaning_fee"] == 170.0
                assert listed["platform_fee_percent"] == 15.0

                update_response = await client.put(
                    f"/api/v1/properties/{prop.id}",
                    headers={"Authorization": "Bearer test-token"},
                    json={
                        "name": prop.name,
                        "property_value": 400000,
                        "monthly_depreciation_percent": 1,
                        "default_cleaning_fee": 250,
                        "platform_fee_percent": 18,
                    },
                )
                assert update_response.status_code == 200
                updated = update_response.json()["data"]
                assert updated["default_cleaning_fee"] == 250.0
                assert updated["platform_fee_percent"] == 18.0

                get_response = await client.get(
                    f"/api/v1/properties/{prop.id}",
                    headers={"Authorization": "Bearer test-token"},
                )
                assert get_response.status_code == 200
                fetched = get_response.json()["data"]
                assert fetched["default_cleaning_fee"] == 250.0
                assert fetched["platform_fee_percent"] == 18.0
        finally:
            app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
