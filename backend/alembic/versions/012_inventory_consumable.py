"""Mark inventory/checklist items as consumable supplies

Revision ID: 012_inventory_consumable
Revises: 011_checklist_incident_image
Create Date: 2026-10-29
"""

from alembic import op
import sqlalchemy as sa


revision = "012_inventory_consumable"
down_revision = "011_checklist_incident_image"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "property_inventory_items",
        sa.Column("is_consumable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "stay_checklist_items",
        sa.Column("is_consumable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("stay_checklist_items", "is_consumable")
    op.drop_column("property_inventory_items", "is_consumable")
