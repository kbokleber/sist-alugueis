"""Add detail fields to property inventory items

Revision ID: 010_inventory_item_details
Revises: 009_user_app_profile
Create Date: 2026-10-29
"""

from alembic import op
import sqlalchemy as sa


revision = "010_inventory_item_details"
down_revision = "009_user_app_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "property_inventory_items",
        sa.Column("color", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "property_inventory_items",
        sa.Column("serial_number", sa.String(length=150), nullable=True),
    )
    op.add_column(
        "property_inventory_items",
        sa.Column("brand", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "property_inventory_items",
        sa.Column("model", sa.String(length=150), nullable=True),
    )
    op.add_column(
        "property_inventory_items",
        sa.Column("image_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("property_inventory_items", "image_url")
    op.drop_column("property_inventory_items", "model")
    op.drop_column("property_inventory_items", "brand")
    op.drop_column("property_inventory_items", "serial_number")
    op.drop_column("property_inventory_items", "color")
