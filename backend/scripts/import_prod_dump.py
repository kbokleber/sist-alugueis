"""Importa o dump JSON de producao para o SQLite de desenvolvimento.

Uso:
    python scripts/import_prod_dump.py [--dump-dir data/prod_dump] [--db dev.db]

Ordem de insercao respeita as FKs:
    users -> properties -> financial_categories -> rental_revenues
    -> property_expenses -> inventory_categories -> property_inventory_items
    -> stay_checklists -> stay_checklist_items -> audit_logs

Nota sobre UUIDs: o Postgres de producao grava UUIDs canonicos (com hifen,
ex.: "b9ae1c56-6ee2-4062-8ae9-adbd20cf6755"), enquanto o SQLAlchemy com o
tipo `Uuid` no SQLite grava o hex sem hifen (ex.: "b9ae1c566ee240628ae9adbd20cf6755").
Todos os UUIDs sao normalizados para hex durante a importacao, caso contrario
nenhum JOIN por FK funcionam no dev.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DUMP_DIR = BACKEND_DIR / "data" / "prod_dump"
DEFAULT_DB = BACKEND_DIR / "dev.db"

# (tabela, colunas na ordem) espelha o schema Postgres de producao.
TABLES = [
    ("users", [
        "id", "email", "hashed_password", "full_name", "is_active", "is_superuser",
        "created_at", "updated_at", "keycloak_sub", "api_token", "app_profile",
    ]),
    ("properties", [
        "id", "user_id", "code", "name", "address", "image_url", "property_value",
        "monthly_depreciation_percent", "default_cleaning_fee", "platform_fee_percent",
        "is_active", "created_at", "updated_at",
    ]),
    ("financial_categories", [
        "id", "user_id", "name", "type", "color", "icon", "is_system", "created_at",
    ]),
    ("rental_revenues", [
        "id", "user_id", "property_id", "year_month", "date", "checkin_date",
        "checkout_date", "guest_name", "listing_name", "listing_source", "nights",
        "gross_amount", "cleaning_fee", "platform_fee", "net_amount", "pending_amount",
        "external_id", "notes", "created_at", "updated_at",
    ]),
    ("property_expenses", [
        "id", "user_id", "property_id", "category_id", "year_month", "name", "amount",
        "is_reserve", "due_date", "paid_date", "status", "source", "notes",
        "created_at", "updated_at",
    ]),
    ("inventory_categories", [
        "id", "property_id", "name", "sort_order", "is_active", "created_at", "updated_at",
    ]),
    ("property_inventory_items", [
        "id", "property_id", "category_id", "name", "quantity_expected", "color",
        "serial_number", "brand", "model", "image_url", "notes", "is_consumable",
        "is_active", "created_at", "updated_at",
    ]),
    ("stay_checklists", [
        "id", "property_id", "rental_revenue_id", "checklist_type", "status",
        "performed_by_user_id", "performed_at", "general_notes", "has_incidents",
        "created_at", "updated_at",
    ]),
    ("stay_checklist_items", [
        "id", "checklist_id", "inventory_item_id", "item_name", "category_name",
        "quantity_expected", "quantity_found", "condition", "incident_notes",
        "incident_image_url", "is_consumable", "sort_order", "created_at", "updated_at",
    ]),
    ("audit_logs", [
        "id", "user_id", "action", "entity_type", "entity_id", "old_values",
        "new_values", "ip_address", "user_agent", "created_at",
    ]),
]

# Colunas que guardam UUID e por isso precisam ser normalizadas para hex.
UUID_COLUMNS = {
    "id", "user_id", "property_id", "category_id", "rental_revenue_id",
    "checklist_id", "inventory_item_id", "entity_id", "performed_by_user_id",
}

# Colunas JSON que viram JSON serializado no SQLite.
JSON_COLUMNS = {"old_values", "new_values"}

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def normalize_uuid(value):
    """Converte UUID canonico (com hifen) para hex de 32 chars (formato SQLite)."""
    if not isinstance(value, str):
        return value
    if UUID_RE.match(value):
        return value.replace("-", "").lower()
    return value


def _normalize_json_value(value):
    """Normaliza recursivamente UUIDs dentro de colunas JSON."""
    if isinstance(value, str):
        return normalize_uuid(value)
    if isinstance(value, dict):
        return {k: _normalize_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_json_value(v) for v in value]
    return value


def _adapt(value):
    """Normaliza tipos vindos do json_agg do Postgres para o SQLite."""
    if value is None or isinstance(value, (str, int, float, bytes)):
        return value
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def load_table(dump_dir, table):
    path = dump_dir / (table + ".json")
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    return json.loads(raw)


def truncate_all(conn):
    tables = [t for t, _ in reversed(TABLES)]
    conn.execute("PRAGMA foreign_keys = OFF")
    for table in tables:
        conn.execute("DELETE FROM " + table)
    conn.execute("PRAGMA foreign_keys = ON")


def import_table(conn, table, columns, rows):
    if not rows:
        print("  %s: vazio" % table)
        return 0

    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(columns)
    sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, column_list, placeholders)

    payload = []
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column)
            if column in UUID_COLUMNS:
                value = normalize_uuid(value)
            elif column in JSON_COLUMNS and value is not None:
                value = json.dumps(_normalize_json_value(value), ensure_ascii=False)
            values.append(_adapt(value))
        payload.append(tuple(values))

    conn.executemany(sql, payload)
    print("  %s: %d linha(s)" % (table, len(payload)))
    return len(payload)


def sync_alembic_version(conn, dump_dir):
    version_file = dump_dir / "_alembic_version.txt"
    if not version_file.exists():
        return
    version = version_file.read_text(encoding="utf-8").strip()
    if not version:
        return
    conn.execute("DELETE FROM alembic_version")
    conn.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (version,))
    print("  alembic_version: %s" % version)


def verify(conn):
    """Confere que os relacionamentos por FK funcionam de fato."""
    checks = [
        ("revenues -> properties",
         "SELECT COUNT(*) FROM rental_revenues r JOIN properties p ON p.id = r.property_id"),
        ("revenues -> users",
         "SELECT COUNT(*) FROM rental_revenues r JOIN users u ON u.id = r.user_id"),
        ("expenses -> properties",
         "SELECT COUNT(*) FROM property_expenses e JOIN properties p ON p.id = e.property_id"),
        ("expenses -> categories",
         "SELECT COUNT(*) FROM property_expenses e JOIN financial_categories c ON c.id = e.category_id"),
        ("inv. categories -> properties",
         "SELECT COUNT(*) FROM inventory_categories i JOIN properties p ON p.id = i.property_id"),
        ("audit -> users",
         "SELECT COUNT(*) FROM audit_logs a JOIN users u ON u.id = a.user_id"),
    ]
    print("\nJoins por FK:")
    for label, sql in checks:
        count = conn.execute(sql).fetchone()[0]
        print("  %-32s %d" % (label, count))


def main():
    parser = argparse.ArgumentParser(description="Importa dump de producao para o SQLite dev.")
    parser.add_argument("--dump-dir", type=Path, default=DEFAULT_DUMP_DIR)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Nao apaga as tabelas antes de importar.",
    )
    args = parser.parse_args()

    if not args.dump_dir.exists():
        raise SystemExit("Diretorio do dump nao encontrado: %s" % args.dump_dir)

    if not args.db.exists():
        raise SystemExit("Banco SQLite nao encontrado: %s" % args.db)

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = OFF")

    try:
        if not args.keep_existing:
            print("Limpando tabelas existentes...")
            truncate_all(conn)

        print("Importando de %s para %s" % (args.dump_dir, args.db))
        total = 0
        for table, columns in TABLES:
            rows = load_table(args.dump_dir, table)
            total += import_table(conn, table, columns, rows)

        sync_alembic_version(conn, args.dump_dir)
        conn.commit()

        print("\nTotal importado: %d linha(s)" % total)
        print("\nVerificacao:")
        for table, _ in TABLES:
            count = conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
            print("  %s: %d" % (table, count))
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        orphans = conn.execute("PRAGMA foreign_key_check").fetchall()
        if orphans:
            print("\nAVISO: %d violacao(oes) de FK:" % len(orphans))
            for row in orphans[:10]:
                print("  %s" % (row,))
        else:
            print("\nIntegridade referencial: OK")
        verify(conn)
        conn.close()


if __name__ == "__main__":
    main()
