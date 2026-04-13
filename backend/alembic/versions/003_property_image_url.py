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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("properties")}
    if "image_url" not in columns:
        op.add_column("properties", sa.Column("image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("properties")}
    if "image_url" in columns:
        op.drop_column("properties", "image_url")
