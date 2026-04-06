#!/usr/bin/env python
"""Seed initial data: admin user + default categories."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import User, FinancialCategory, CategoryType
from app.utils.security import hash_password


ADMIN_EMAIL = "admin@sistalugueis.com"
ADMIN_PASSWORD = "Admin@123"
ADMIN_NAME = "Administrador"


async def seed():
    async with AsyncSessionLocal() as db:
        # Check if admin exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Admin user already exists: {ADMIN_EMAIL}")
            admin = existing
        else:
            admin = User(
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                full_name=ADMIN_NAME,
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            print(f"Created admin user: {ADMIN_EMAIL}")

        # Seed default categories
        defaults = [
            {"name": "Limpeza", "type": CategoryType.EXPENSE, "color": "#FF6B6B", "icon": "sparkles", "is_system": True},
            {"name": "Manutenção", "type": CategoryType.EXPENSE, "color": "#4ECDC4", "icon": "wrench", "is_system": True},
            {"name": "Taxa Administrativa", "type": CategoryType.EXPENSE, "color": "#45B7D1", "icon": "percent", "is_system": True},
            {"name": "Condomínio", "type": CategoryType.EXPENSE, "color": "#FFA07A", "icon": "building", "is_system": True},
            {"name": "IPTU", "type": CategoryType.EXPENSE, "color": "#98D8C8", "icon": "landmark", "is_system": True},
            {"name": "Taxa de Limpeza", "type": CategoryType.REVENUE, "color": "#A8E6CF", "icon": "sparkles", "is_system": True},
            {"name": "Aluguel", "type": CategoryType.REVENUE, "color": "#88D8B0", "icon": "home", "is_system": True},
            {"name": "Taxa Airbnb", "type": CategoryType.EXPENSE, "color": "#FF5E7D", "icon": "airbnb", "is_system": True},
            {"name": "Contas de Consumo", "type": CategoryType.EXPENSE, "color": "#F7DC6F", "icon": "zap", "is_system": True},
            {"name": "Outros", "type": CategoryType.EXPENSE, "color": "#BDBDBD", "icon": "more", "is_system": True},
        ]

        for cat_data in defaults:
            result = await db.execute(
                select(FinancialCategory).where(
                    FinancialCategory.user_id == admin.id,
                    FinancialCategory.name == cat_data["name"],
                )
            )
            if result.scalar_one_or_none() is None:
                cat = FinancialCategory(user_id=admin.id, **cat_data)
                db.add(cat)
                print(f"  Created category: {cat_data['name']}")

        await db.commit()
        print("Seed completed successfully!")
        print(f"\nAdmin credentials:")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
