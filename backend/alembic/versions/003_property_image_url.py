"""add image_url to properties

Revision ID: 003_property_image
Revises: 002_pending_amount
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa


revision = "003_property_image"
down_revision = "002_pending_amount"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("properties", "image_url")
