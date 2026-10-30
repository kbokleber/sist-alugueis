import uuid
from decimal import Decimal
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.dependencies import get_current_user
from app.main import app
from app.models import Property, RentalRevenue, User


@pytest.mark.asyncio
async def test_inventory_and_checklist_flow():
    engine = create_async_engine("sqlite+aiosqlite:///./test_inventory_api.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db_session:
        user = User(
            id=uuid.uuid4(),
            email="inventory-api@test.com",
            hashed_password="hashed",
            full_name="Inventory API Test",
            is_active=True,
            is_superuser=False,
        )
        prop = Property(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Casa Inventário",
            property_value=Decimal("300000.00"),
            monthly_depreciation_percent=Decimal("1.00"),
            default_cleaning_fee=Decimal("170.00"),
            platform_fee_percent=Decimal("15.00"),
            is_active=True,
        )
        revenue = RentalRevenue(
            id=uuid.uuid4(),
            user_id=user.id,
            property_id=prop.id,
            year_month="2026-10",
            date=date(2026, 10, 1),
            checkin_date=date(2026, 10, 1),
            checkout_date=date(2026, 10, 5),
            guest_name="Hóspede Teste",
            nights=4,
            gross_amount=Decimal("1000.00"),
            cleaning_fee=Decimal("170.00"),
            platform_fee=Decimal("150.00"),
            net_amount=Decimal("680.00"),
        )
        db_session.add_all([user, prop, revenue])
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
                headers = {"Authorization": "Bearer test-token"}

                cat_resp = await client.post(
                    f"/api/v1/properties/{prop.id}/inventory-categories",
                    headers=headers,
                    json={"name": "Cozinha", "sort_order": 1},
                )
                assert cat_resp.status_code == 201, cat_resp.text
                category_id = cat_resp.json()["data"]["id"]

                item_resp = await client.post(
                    f"/api/v1/properties/{prop.id}/inventory-items",
                    headers=headers,
                    json={
                        "category_id": category_id,
                        "name": "Cadeira",
                        "quantity_expected": 4,
                        "color": "Marrom",
                        "serial_number": "SN-123",
                        "brand": "Tok&Stok",
                        "model": "Classic",
                        "image_url": "data:image/png;base64,abc",
                        "notes": "Madeira",
                    },
                )
                assert item_resp.status_code == 201, item_resp.text
                item_data = item_resp.json()["data"]
                item_id = item_data["id"]
                assert item_data["category_name"] == "Cozinha"
                assert item_data["color"] == "Marrom"
                assert item_data["serial_number"] == "SN-123"
                assert item_data["brand"] == "Tok&Stok"
                assert item_data["model"] == "Classic"
                assert item_data["image_url"] == "data:image/png;base64,abc"

                list_items = await client.get(
                    f"/api/v1/properties/{prop.id}/inventory-items",
                    headers=headers,
                )
                assert list_items.status_code == 200
                assert len(list_items.json()["data"]) == 1

                checklist_resp = await client.post(
                    f"/api/v1/revenues/{revenue.id}/checklists",
                    headers=headers,
                    json={"checklist_type": "checkin"},
                )
                assert checklist_resp.status_code == 201, checklist_resp.text
                checklist = checklist_resp.json()["data"]
                assert len(checklist["items"]) == 1
                assert checklist["items"][0]["item_name"] == "Cadeira"
                checklist_id = checklist["id"]
                line_id = checklist["items"][0]["id"]

                update_resp = await client.put(
                    f"/api/v1/checklists/{checklist_id}/items",
                    headers=headers,
                    json={
                        "general_notes": "Visita de entrada",
                        "items": [
                            {
                                "id": line_id,
                                "quantity_found": 3,
                                "condition": "damaged",
                                "incident_notes": "Uma cadeira com assento rasgado",
                            }
                        ],
                    },
                )
                assert update_resp.status_code == 200, update_resp.text
                updated = update_resp.json()["data"]
                assert updated["has_incidents"] is True
                assert updated["items"][0]["condition"] == "damaged"

                complete_resp = await client.post(
                    f"/api/v1/checklists/{checklist_id}/complete",
                    headers=headers,
                )
                assert complete_resp.status_code == 200, complete_resp.text
                completed = complete_resp.json()["data"]
                assert completed["status"] == "completed"
                assert completed["has_incidents"] is True
                assert completed["performed_by_name"] == user.full_name
                assert completed["performed_by_user_id"] == str(user.id)

                delete_item = await client.delete(
                    f"/api/v1/inventory-items/{item_id}",
                    headers=headers,
                )
                assert delete_item.status_code == 200
                active_items = await client.get(
                    f"/api/v1/properties/{prop.id}/inventory-items",
                    headers=headers,
                )
                assert active_items.json()["data"] == []
        finally:
            app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
