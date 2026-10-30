"""Add incident_image_url to stay checklist items

Revision ID: 011_checklist_incident_image
Revises: 010_inventory_item_details
Create Date: 2026-10-29
"""

from alembic import op
import sqlalchemy as sa


revision = "011_checklist_incident_image"
down_revision = "010_inventory_item_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stay_checklist_items",
        sa.Column("incident_image_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("stay_checklist_items", "incident_image_url")
