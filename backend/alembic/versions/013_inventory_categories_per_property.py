"""inventory categories scoped by property

Revision ID: 013_inv_cat_property
Revises: 012_inventory_consumable
Create Date: 2026-10-30
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_inv_cat_property"
down_revision: Union[str, None] = "012_inventory_consumable"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)

    if "inventory_categories" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("inventory_categories")}
    if "property_id" in cols and "user_id" not in cols:
        return

    # SQLite: o ensure_inventory_categories_property_scope() no app faz a troca.
    if dialect == "sqlite":
        return

    if "property_id" not in cols:
        op.add_column(
            "inventory_categories",
            sa.Column("property_id", sa.Uuid(), nullable=True),
        )
        op.create_foreign_key(
            "fk_inventory_categories_property_id",
            "inventory_categories",
            "properties",
            ["property_id"],
            ["id"],
        )

    # Associa categorias existentes a um imóvel via itens (quando houver)
    op.execute(
        sa.text(
            """
            UPDATE inventory_categories AS ic
            SET property_id = sub.property_id
            FROM (
                SELECT DISTINCT ON (pii.category_id)
                    pii.category_id,
                    pii.property_id
                FROM property_inventory_items AS pii
                ORDER BY pii.category_id, pii.created_at
            ) AS sub
            WHERE ic.id = sub.category_id
              AND ic.property_id IS NULL
            """
        )
    )

    # Categorias órfãs (sem imóvel) não servem no novo modelo
    op.execute(sa.text("DELETE FROM inventory_categories WHERE property_id IS NULL"))
    op.alter_column("inventory_categories", "property_id", nullable=False)

    # Remove vínculo antigo com usuário
    for fk in inspector.get_foreign_keys("inventory_categories"):
        if fk.get("constrained_columns") == ["user_id"] and fk.get("name"):
            op.drop_constraint(fk["name"], "inventory_categories", type_="foreignkey")

    try:
        op.drop_constraint(
            "uq_inventory_categories_user_name",
            "inventory_categories",
            type_="unique",
        )
    except Exception:
        pass

    try:
        op.drop_index(
            "ix_inventory_categories_user_id",
            table_name="inventory_categories",
        )
    except Exception:
        pass

    if "user_id" in cols:
        op.drop_column("inventory_categories", "user_id")

    # Recria unique/index por imóvel
    existing_uniques = {
        uq.get("name") for uq in inspector.get_unique_constraints("inventory_categories")
    }
    if "uq_inventory_categories_property_name" not in existing_uniques:
        op.create_unique_constraint(
            "uq_inventory_categories_property_name",
            "inventory_categories",
            ["property_id", "name"],
        )

    existing_indexes = {idx.get("name") for idx in inspector.get_indexes("inventory_categories")}
    if "ix_inventory_categories_property_id" not in existing_indexes:
        op.create_index(
            "ix_inventory_categories_property_id",
            "inventory_categories",
            ["property_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    op.add_column(
        "inventory_categories",
        sa.Column("user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_inventory_categories_user_id",
        "inventory_categories",
        "users",
        ["user_id"],
        ["id"],
    )
    try:
        op.drop_constraint(
            "uq_inventory_categories_property_name",
            "inventory_categories",
            type_="unique",
        )
    except Exception:
        pass
    try:
        op.drop_index(
            "ix_inventory_categories_property_id",
            table_name="inventory_categories",
        )
    except Exception:
        pass
    try:
        op.drop_constraint(
            "fk_inventory_categories_property_id",
            "inventory_categories",
            type_="foreignkey",
        )
    except Exception:
        pass
    op.drop_column("inventory_categories", "property_id")
