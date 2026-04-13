#!/usr/bin/env python3
"""Import historic data from Google Sheets CSV exports.

Usage:
    python -m scripts.import_historic_data

The script imports:
- Properties (2 imóveis: QD03H, AF01J)
- Revenues (~1100 rental records)
- Expenses (~369 expense records)
"""

import asyncio
import csv
import os
import sys
from datetime import datetime, date
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import (
    User, Property, FinancialCategory, CategoryType,
    RentalRevenue, PropertyExpense, ExpenseStatus, ExpenseSource
)
from sqlalchemy import select

DATA_DIR = "/data/workspace/sist-alugueis/data"
ADMIN_EMAIL = "admin@sistalugueis.com"


def parse_brazilian_currency(value: str) -> Decimal:
    """Convert 'R$ 1.234,56' to Decimal."""
    if not value or value.strip() == "":
        return Decimal("0")
    cleaned = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return Decimal(cleaned)
    except Exception:
        return Decimal("0")


def parse_brazilian_date(value: str) -> date | None:
    """Parse 'DD/MM/YYYY' to date."""
    if not value or value.strip() == "":
        return None
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date()
    except Exception:
        return None


def parse_month_ref(value: str) -> str | None:
    """Parse '2023/04' to '2023-04'."""
    if not value or value.strip() == "":
        return None
    return value.strip().replace("/", "-")


def normalize_booking_code(value: str) -> str:
    """Normalize booking code for consistent matching."""
    return (value or "").strip().upper()


def normalize_guest_name(value: str) -> str:
    """Normalize guest name spacing."""
    return " ".join((value or "").strip().split())


def is_generic_guest_name(value: str) -> bool:
    """Detect placeholder guest names."""
    normalized = normalize_guest_name(value).casefold()
    return (
        not normalized
        or normalized == "hóspede sem nome"
        or normalized == "hospede sem nome"
        or normalized.startswith("hospede ")
        or normalized.startswith("hóspede ")
    )


async def get_admin_user(db) -> User:
    """Get or create admin user."""
    result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
    user = result.scalar_one_or_none()
    if not user:
        # Try to find any superuser
        result = await db.execute(select(User).where(User.is_superuser == True).limit(1))
        user = result.scalar_one_or_none()
    if not user:
        # Try to find any user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
    if not user:
        raise RuntimeError("No admin/user found. Run seed_data.py first.")
    return user


async def import_properties(db, admin_user_id: int) -> dict:
    """Import properties from properties.csv."""
    properties_csv = os.path.join(DATA_DIR, "properties.csv")

    print("\n=== Importing Properties ===")

    property_map = {
        "Andorinhas": {"code": "QD03H", "name": "Andorinha 301 - Guaruja"},
        "Ondomingos": {"code": "AF01J", "name": "On Domingos de Morais 1507"},
    }

    created_properties = {}

    with open(properties_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)  # Skip header

        for row in reader:
            if len(row) < 3:
                continue

            nome_imovel = row[0].strip()
            valuation = parse_brazilian_currency(row[1])
            reference_percentage = Decimal("1.0")  # 1%

            if nome_imovel in property_map:
                prop_data = property_map[nome_imovel]

                result = await db.execute(
                    select(Property).where(Property.name == prop_data["name"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"  [exists] {prop_data['name']} (val: R${valuation})")
                    created_properties[nome_imovel] = existing
                else:
                    prop = Property(
                        user_id=admin_user_id,
                        name=prop_data["name"],
                        address=f"Imóvel {nome_imovel}",
                        property_value=float(valuation),
                        monthly_depreciation_percent=float(reference_percentage),
                        is_active=True,
                    )
                    db.add(prop)
                    await db.flush()
                    created_properties[nome_imovel] = prop
                    print(f"  [created] {prop_data['name']} (val: R${valuation})")

    await db.commit()
    return created_properties


async def get_or_create_categories(db, admin_user_id: int) -> dict:
    """Ensure all needed categories exist."""
    categories = {
        "Limpeza": CategoryType.EXPENSE,
        "Taxa ADM": CategoryType.EXPENSE,
        "Taxa Administrativa": CategoryType.EXPENSE,
        "Condomínio": CategoryType.EXPENSE,
        "IPTU": CategoryType.EXPENSE,
        "Energia elétrica": CategoryType.EXPENSE,
        "Internet": CategoryType.EXPENSE,
        "Manutenção/Reforma": CategoryType.EXPENSE,
        "Contas de Consumo": CategoryType.EXPENSE,
        "Aluguel": CategoryType.REVENUE,
        "Taxa Airbnb": CategoryType.EXPENSE,
        "Ar condicionado": CategoryType.EXPENSE,
        "Comissão Corretor": CategoryType.EXPENSE,
        "Desconto hóspede": CategoryType.EXPENSE,
        "Despesa extra": CategoryType.EXPENSE,
        "Dízimo": CategoryType.EXPENSE,
        "Gás": CategoryType.EXPENSE,
        "Taxa Enxoval": CategoryType.EXPENSE,
        "Elektro": CategoryType.EXPENSE,
        "Outros": CategoryType.EXPENSE,
    }

    cat_map = {}
    for name, cat_type in categories.items():
        result = await db.execute(
            select(FinancialCategory).where(
                FinancialCategory.name == name,
                FinancialCategory.user_id == admin_user_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            cat_map[name] = existing
        else:
            cat = FinancialCategory(
                user_id=admin_user_id,
                name=name,
                type=cat_type,
                is_system=True,
            )
            db.add(cat)
            await db.flush()
            cat_map[name] = cat

    await db.commit()
    return cat_map


async def import_revenues(db, admin_user_id: int, properties: dict) -> int:
    """Import revenues from revenues.csv. Returns count of imported records."""
    revenues_csv = os.path.join(DATA_DIR, "revenues.csv")

    print("\n=== Importing Revenues ===")

    prop_name_to_code = {
        "Andorinhas": "QD03H",
        "Ondomingos": "AF01J",
    }

    # Property name → Property ORM object
    prop_objects = {}
    for prop_name, prop in properties.items():
        prop_objects[prop_name] = prop
        prop_objects[prop_name_to_code.get(prop_name, "")] = prop

    count = 0
    skipped = 0
    updated = 0
    errors = 0

    with open(revenues_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)  # Skip header

        for row_idx, row in enumerate(reader, start=2):
            if len(row) < 13:
                skipped += 1
                continue

            try:
                data_pagamento = parse_brazilian_date(row[0])
                data_inicio = parse_brazilian_date(row[1])
                data_saida = parse_brazilian_date(row[2])
                mes_ref = parse_month_ref(row[3])
                noites_str = row[4].strip()
                hospede = normalize_guest_name(row[5])
                anuncio = row[6].strip()
                valor_cobrado = parse_brazilian_currency(row[7])
                limpeza = parse_brazilian_currency(row[8])
                taxa_adm = parse_brazilian_currency(row[9])
                valor_liquido = parse_brazilian_currency(row[10])
                api_airbnb = parse_brazilian_currency(row[11]) if len(row) > 11 else Decimal("0")
                reserva = normalize_booking_code(row[12]) if len(row) > 12 else ""

                if not noites_str:
                    noites = 0
                else:
                    try:
                        noites = int(noites_str)
                    except Exception:
                        noites = 0

                # Get property object
                prop_code = prop_name_to_code.get(anuncio)
                if not prop_code:
                    errors += 1
                    if errors <= 5:
                        print(f"  [warn] Row {row_idx}: Unknown property '{anuncio}'")
                    continue

                prop = properties.get(anuncio)
                if not prop:
                    errors += 1
                    if errors <= 5:
                        print(f"  [warn] Row {row_idx}: Property not found for '{anuncio}'")
                    continue

                # Skip if no valid date
                if not data_pagamento:
                    skipped += 1
                    continue

                # Check if already exists (by booking code)
                if reserva:
                    result = await db.execute(
                        select(RentalRevenue).where(
                            RentalRevenue.external_id == reserva,
                            RentalRevenue.user_id == admin_user_id,
                        )
                    )
                    existing = result.scalar_one_or_none()
                    if existing:
                        has_real_name_from_file = bool(hospede) and not is_generic_guest_name(hospede)
                        existing_is_generic = is_generic_guest_name(existing.guest_name)
                        if has_real_name_from_file and existing_is_generic:
                            existing.guest_name = hospede
                            updated += 1
                        else:
                            skipped += 1
                        continue

                rev = RentalRevenue(
                    user_id=admin_user_id,
                    property_id=prop.id,
                    year_month=mes_ref or "",
                    date=data_pagamento,
                    checkin_date=data_inicio,
                    checkout_date=data_saida,
                    guest_name=hospede or "Hóspede sem nome",
                    listing_name=anuncio,
                    listing_source="Airbnb" if reserva else "Manual",
                    nights=noites,
                    gross_amount=float(valor_cobrado),
                    cleaning_fee=float(limpeza),
                    platform_fee=float(taxa_adm),
                    net_amount=float(valor_liquido),
                    external_id=reserva or None,
                )
                db.add(rev)
                count += 1

                # Commit in batches
                if count % 200 == 0:
                    await db.commit()
                    print(f"  Committed {count} revenues...")

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  [error] Row {row_idx}: {e}")

    await db.commit()
    if updated:
        await db.commit()
    print(
        f"  Done! Imported: {count}, Updated guests: {updated}, "
        f"Skipped (duplicates): {skipped}, Errors: {errors}"
    )
    return count


async def import_expenses(db, admin_user_id: int, properties: dict, categories: dict) -> int:
    """Import expenses from expenses.csv. Returns count of imported records."""
    expenses_csv = os.path.join(DATA_DIR, "expenses.csv")

    print("\n=== Importing Expenses ===")

    prop_name_to_code = {
        "Andorinhas": "QD03H",
        "Ondomingos": "AF01J",
    }

    # Category name normalization
    cat_normalize = {
        "Energia elétrica": "Energia elétrica",
        "Energia": "Energia elétrica",
        "IPTU": "IPTU",
        "Condomínio": "Condomínio",
        "Taxa ADM": "Taxa ADM",
        "Taxa Administrativa": "Taxa Administrativa",
        "Limpeza": "Limpeza",
        "Internet": "Internet",
        "Internet Claro": "Internet",
        "Manutenção/Reforma": "Manutenção/Reforma",
        "Manutenção": "Manutenção/Reforma",
        "manutenção/Reforma": "Manutenção/Reforma",
        "Ar condicionado": "Ar condicionado",
        "Comissão Corretor": "Comissão Corretor",
        "Desconto hóspede": "Desconto hóspede",
        "Despesa extra": "Despesa extra",
        "Dízimo": "Dízimo",
        "Gás": "Gás",
        "Taxa Enxoval": "Taxa Enxoval",
        "Elektro": "Elektro",
        "Contas de Consumo": "Contas de Consumo",
        "Outros": "Outros",
    }

    def get_category(name: str):
        normalized = cat_normalize.get(name, name)
        return categories.get(normalized)

    def get_default_category():
        return categories.get("Outros")

    count = 0
    skipped = 0
    errors = 0

    with open(expenses_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)  # Skip header

        for row_idx, row in enumerate(reader, start=2):
            if len(row) < 4:
                skipped += 1
                continue

            try:
                anuncio = row[0].strip()
                nome_despesa = row[1].strip()
                mes_ref = parse_month_ref(row[2])
                valor_despesa = parse_brazilian_currency(row[3])
                reserva = row[4].strip() if len(row) > 4 else ""

                # Reserve flag: "Reserva" contains Airbnb booking codes when expense
                # is linked to a specific booking. Non-empty = linked to a booking.
                is_reserve = False  # These are regular expenses, not reserve funds

                # Get property
                prop = properties.get(anuncio)
                if not prop:
                    errors += 1
                    if errors <= 5:
                        print(f"  [warn] Row {row_idx}: Property not found for '{anuncio}'")
                    continue

                # Get category
                cat = get_category(nome_despesa)
                if not cat:
                    cat = get_default_category()
                    if errors <= 3:
                        print(f"  [warn] Row {row_idx}: Category '{nome_despesa}' not found, using 'Outros'")

                if not cat:
                    errors += 1
                    continue

                # Check for duplicate (same property + category + amount + month + name)
                result = await db.execute(
                    select(PropertyExpense).where(
                        PropertyExpense.property_id == prop.id,
                        PropertyExpense.category_id == cat.id,
                        PropertyExpense.name == nome_despesa,
                        PropertyExpense.year_month == mes_ref,
                        PropertyExpense.user_id == admin_user_id,
                    )
                )
                existing = result.scalar_one_or_none()
                if existing:
                    skipped += 1
                    continue

                expense = PropertyExpense(
                    user_id=admin_user_id,
                    property_id=prop.id,
                    category_id=cat.id,
                    year_month=mes_ref or "",
                    name=nome_despesa,
                    amount=float(valor_despesa),
                    is_reserve=is_reserve,
                    status=ExpenseStatus.PAID if not is_reserve else ExpenseStatus.PENDING,
                    source=ExpenseSource.SCRIPT,
                    notes=f"Importado de planilha (reserva: {reserva})" if reserva else "Importado de planilha",
                )
                db.add(expense)
                count += 1

                if count % 200 == 0:
                    await db.commit()
                    print(f"  Committed {count} expenses...")

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  [error] Row {row_idx}: {e}")

    await db.commit()
    print(f"  Done! Imported: {count}, Skipped (duplicates): {skipped}, Errors: {errors}")
    return count


async def main():
    print("=" * 60)
    print("Historic Data Import - sist-alugueis")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # Get admin user
        admin_user = await get_admin_user(db)
        print(f"\nUsing admin user: {admin_user.email} (id: {admin_user.id})")

        # Import properties
        properties = await import_properties(db, admin_user.id)
        if not properties:
            print("ERROR: No properties imported. Check the CSV file.")
            return

        # Import categories
        categories = await get_or_create_categories(db, admin_user.id)
        print(f"\nCategories available: {list(categories.keys())}")

        # Import revenues
        rev_count = await import_revenues(db, admin_user.id, properties)

        # Import expenses
        exp_count = await import_expenses(db, admin_user.id, properties, categories)

        print("\n" + "=" * 60)
        print("Import Summary")
        print("=" * 60)
        print(f"  Properties imported: {len(properties)}")
        print(f"  Revenues imported:   {rev_count}")
        print(f"  Expenses imported:   {exp_count}")
        print("=" * 60)
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
