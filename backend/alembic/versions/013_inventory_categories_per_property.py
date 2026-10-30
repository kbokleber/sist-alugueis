"""inventory categories scoped by property

Revision ID: 013
Revises: 012
Create Date: 2026-10-30

Nota: em SQLite o app também aplica ensure_inventory_categories_property_scope()
no startup (recria a tabela com segurança).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("inventory_categories")}
    if "property_id" in cols and "user_id" not in cols:
        return

    # Delega a lógica pesada ao ensure do app em SQLite; em Postgres aplica DDL.
    dialect = bind.dialect.name
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

    op.execute(
        sa.text(
            """
            UPDATE inventory_categories ic
            SET property_id = sub.property_id
            FROM (
                SELECT DISTINCT ON (pii.category_id) pii.category_id, pii.property_id
                FROM property_inventory_items pii
                ORDER BY pii.category_id, pii.created_at
            ) AS sub
            WHERE ic.id = sub.category_id AND ic.property_id IS NULL
            """
        )
    )
    op.execute(sa.text("DELETE FROM inventory_categories WHERE property_id IS NULL"))
    op.alter_column("inventory_categories", "property_id", nullable=False)
    op.drop_constraint("uq_inventory_categories_user_name", "inventory_categories", type_="unique")
    op.drop_index("ix_inventory_categories_user_id", table_name="inventory_categories")
    op.drop_column("inventory_categories", "user_id")
    op.create_unique_constraint(
        "uq_inventory_categories_property_name",
        "inventory_categories",
        ["property_id", "name"],
    )
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
    op.drop_constraint("uq_inventory_categories_property_name", "inventory_categories", type_="unique")
    op.drop_index("ix_inventory_categories_property_id", table_name="inventory_categories")
    op.drop_constraint("fk_inventory_categories_property_id", "inventory_categories", type_="foreignkey")
    op.drop_column("inventory_categories", "property_id")
