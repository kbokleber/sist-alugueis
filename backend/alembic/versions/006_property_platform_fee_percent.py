"""replace default_platform_fee with platform_fee_percent

Revision ID: 006_platform_fee_pct
Revises: 005_property_financial_defaults
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa


revision = "006_platform_fee_pct"
down_revision = "005_property_financial_defaults"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("properties")}

    if "platform_fee_percent" not in columns:
        op.add_column(
            "properties",
            sa.Column(
                "platform_fee_percent",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="15.00",
            ),
        )

    if "default_platform_fee" in columns:
        op.drop_column("properties", "default_platform_fee")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("properties")}

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

    if "platform_fee_percent" in columns:
        op.drop_column("properties", "platform_fee_percent")
