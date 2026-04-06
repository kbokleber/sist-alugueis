#!/usr/bin/env python
"""Seed initial data: admin user + default categories + properties + sample financial data."""
import asyncio
import os
import sys
import uuid
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import (
    User, FinancialCategory, CategoryType,
    Property, RentalRevenue, PropertyExpense, ExpenseStatus
)
from app.utils.security import hash_password


ADMIN_EMAIL = "admin@sistalugueis.com"
ADMIN_PASSWORD = "Admin@123"
ADMIN_NAME = "Administrador"


async def seed():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # Check if admin exists
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

        categories = {}
        for cat_data in defaults:
            result = await db.execute(
                select(FinancialCategory).where(
                    FinancialCategory.user_id == admin.id,
                    FinancialCategory.name == cat_data["name"],
                )
            )
            cat = result.scalar_one_or_none()
            if cat is None:
                cat = FinancialCategory(user_id=admin.id, **cat_data)
                db.add(cat)
                print(f"  Created category: {cat_data['name']}")
            categories[cat_data["name"]] = cat

        await db.commit()

        # Seed properties
        properties_data = [
            {
                "name": "AF01J - Ondomingos",
                "address": "Rua das Ondas, 100 - Domingos",
                "property_value": Decimal("450000.00"),
            },
            {
                "name": "QD03H - Andorinha",
                "address": "Av. das Andorinhas, 250 - Quadra 03",
                "property_value": Decimal("620000.00"),
            },
        ]

        properties = {}
        for prop_data in properties_data:
            prop_name = prop_data["name"]
            prop_code = prop_name[:5]  # AF01J or QD03H
            result = await db.execute(
                select(Property).where(
                    Property.user_id == admin.id,
                    Property.name == prop_name,
                )
            )
            prop = result.scalar_one_or_none()
            if prop is None:
                prop = Property(user_id=admin.id, **prop_data)
                db.add(prop)
                print(f"  Created property: {prop_name}")
            properties[prop_code] = prop

        await db.commit()

        # Get all properties again with IDs
        for code in properties:
            await db.refresh(properties[code])

        # Sample data: 6 months (October 2025 to March 2026)
        months = [
            ("2025-10", "2025-10-01"),
            ("2025-11", "2025-11-01"),
            ("2025-12", "2025-12-01"),
            ("2026-01", "2026-01-01"),
            ("2026-02", "2026-02-01"),
            ("2026-03", "2026-03-01"),
        ]

        # Guest names by property
        guest_names = {
            "AF01J": ["Carlos Silva", "Ana Paula", "Roberto Costa", "Maria Fernanda", "João Pedro", "Lucia Mendes"],
            "QD03H": ["Paulo Henrique", "Rosa Almeida", "Fernando Santos", "Carla Oliveira", "Bruno Cardoso", "Juliana Rocha"],
        }

        # Sample revenues per property per month
        for prop_code, prop in properties.items():
            for i, (ym, date_str) in enumerate(months):
                # 2-4 bookings per month
                num_bookings = 2 + (i % 3)

                for j in range(num_bookings):
                    nights = 2 + (j % 5)
                    gross = Decimal(str(180 + (i * 15) + (j * 20)))
                    cleaning = Decimal("80")
                    platform_fee = gross * Decimal("0.12")
                    net = gross - platform_fee

                    d = date.fromisoformat(date_str) + timedelta(days=j * 4)
                    checkout = d + timedelta(days=nights)

                    rev = RentalRevenue(
                        user_id=admin.id,
                        property_id=prop.id,
                        year_month=ym,
                        date=d,
                        checkin_date=d,
                        checkout_date=checkout,
                        guest_name=guest_names[prop_code][j % len(guest_names[prop_code])],
                        listing_name=f"Airbnb {prop.name}",
                        listing_source="Airbnb",
                        nights=nights,
                        gross_amount=gross,
                        cleaning_fee=cleaning,
                        platform_fee=platform_fee,
                        net_amount=net,
                    )
                    db.add(rev)

                print(f"  Created {num_bookings} revenues for {prop_code} ({ym})")

            # Monthly expenses per property
            for i, (ym, date_str) in enumerate(months):
                # Condomínio (monthly)
                condominio = PropertyExpense(
                    user_id=admin.id,
                    property_id=prop.id,
                    category_id=categories["Condomínio"].id,
                    year_month=ym,
                    name="Condomínio mensal",
                    amount=Decimal("450.00") if prop_code == "AF01J" else Decimal("580.00"),
                    is_reserve=False,
                    due_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-05"),
                    status=ExpenseStatus.PAID if i < 5 else ExpenseStatus.PENDING,
                    paid_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-03") if i < 5 else None,
                )
                db.add(condominio)

                # IPTU (monthly portion - only in some months)
                if i % 3 == 0:
                    iptu = PropertyExpense(
                        user_id=admin.id,
                        property_id=prop.id,
                        category_id=categories["IPTU"].id,
                        year_month=ym,
                        name="IPTU Parcela",
                        amount=Decimal("180.00") if prop_code == "AF01J" else Decimal("220.00"),
                        is_reserve=False,
                        due_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-10"),
                        status=ExpenseStatus.PAID if i < 4 else ExpenseStatus.PENDING,
                        paid_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-08") if i < 4 else None,
                    )
                    db.add(iptu)

                # Taxa Administrativa (monthly)
                taxa_adm = PropertyExpense(
                    user_id=admin.id,
                    property_id=prop.id,
                    category_id=categories["Taxa Administrativa"].id,
                    year_month=ym,
                    name="Taxa Administrativa",
                    amount=Decimal("150.00"),
                    is_reserve=False,
                    due_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-15"),
                    status=ExpenseStatus.PAID if i < 5 else ExpenseStatus.PENDING,
                    paid_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-12") if i < 5 else None,
                )
                db.add(taxa_adm)

                # Limpeza (between bookings)
                if i % 2 == 0:
                    limpeza = PropertyExpense(
                        user_id=admin.id,
                        property_id=prop.id,
                        category_id=categories["Limpeza"].id,
                        year_month=ym,
                        name="Limpeza pós-estadia",
                        amount=Decimal("80.00"),
                        is_reserve=False,
                        due_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-20"),
                        status=ExpenseStatus.PAID if i < 5 else ExpenseStatus.PENDING,
                        paid_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-18") if i < 5 else None,
                    )
                    db.add(limpeza)

                # Manutenção (quarterly)
                if i % 3 == 1:
                    manut = PropertyExpense(
                        user_id=admin.id,
                        property_id=prop.id,
                        category_id=categories["Manutenção"].id,
                        year_month=ym,
                        name="Manutenção preventiva",
                        amount=Decimal("200.00"),
                        is_reserve=False,
                        due_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-25"),
                        status=ExpenseStatus.PAID if i < 4 else ExpenseStatus.PENDING,
                        paid_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-22") if i < 4 else None,
                    )
                    db.add(manut)

                # Contas de Consumo (monthly)
                consumo = PropertyExpense(
                    user_id=admin.id,
                    property_id=prop.id,
                    category_id=categories["Contas de Consumo"].id,
                    year_month=ym,
                    name="Contas de consumo",
                    amount=Decimal("95.00"),
                    is_reserve=False,
                    due_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-28"),
                    status=ExpenseStatus.PAID if i < 5 else ExpenseStatus.PENDING,
                    paid_date=date.fromisoformat(f"{ym[:4]}-{ym[5:]}-26") if i < 5 else None,
                )
                db.add(consumo)

                print(f"  Created expenses for {prop_code} ({ym})")

        await db.commit()
        print("\nSeed completed successfully!")
        print(f"\nAdmin credentials:")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD}")
        print(f"\nProperties:")
        for code, prop in properties.items():
            print(f"  {code} - {prop.name}")


if __name__ == "__main__":
    asyncio.run(seed())
