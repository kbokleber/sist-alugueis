"""add default cleaning and platform fee to properties

Revision ID: 005_property_financial_defaults
Revises: 004_expense_source
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa


revision = "005_property_financial_defaults"
down_revision = "004_expense_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("properties")}

    if "default_cleaning_fee" not in columns:
        op.add_column(
            "properties",
            sa.Column(
                "default_cleaning_fee",
                sa.Numeric(15, 2),
                nullable=False,
                server_default="170.00",
            ),
        )
    if "default_platform_fee" not in columns:
        op.add_column(
            "properties",
            sa.Column(
                "default_platform_fee",
                sa.Numeric(15, 2),
                nullable=False,
                server_default="0.00",
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("properties")}

    if "default_platform_fee" in columns:
        op.drop_column("properties", "default_platform_fee")
    if "default_cleaning_fee" in columns:
        op.drop_column("properties", "default_cleaning_fee")
