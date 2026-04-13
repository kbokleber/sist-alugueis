"""add source to property_expenses

Revision ID: 004_expense_source
Revises: 003_property_image
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa


revision = "004_expense_source"
down_revision = "003_property_image"
branch_labels = None
depends_on = None


expense_source_enum = sa.Enum("MANUAL", "SCRIPT", name="expensesource")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("property_expenses")}
    indexes = {index["name"] for index in inspector.get_indexes("property_expenses")}
    expense_source_enum.create(bind, checkfirst=True)
    if "source" not in columns:
        op.add_column(
            "property_expenses",
            sa.Column(
                "source",
                expense_source_enum,
                nullable=False,
                server_default="MANUAL",
            ),
        )
    if "ix_property_expenses_source" not in indexes:
        op.create_index("ix_property_expenses_source", "property_expenses", ["source"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("property_expenses")}
    indexes = {index["name"] for index in inspector.get_indexes("property_expenses")}
    if "ix_property_expenses_source" in indexes:
        op.drop_index("ix_property_expenses_source", table_name="property_expenses")
    if "source" in columns:
        op.drop_column("property_expenses", "source")
    expense_source_enum.drop(bind, checkfirst=True)
