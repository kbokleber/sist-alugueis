"""add pending amount to rental revenues

Revision ID: 002_pending_amount
Revises: 001_initial
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_pending_amount"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("rental_revenues")}
    if "pending_amount" not in columns:
        op.add_column(
            "rental_revenues",
            sa.Column("pending_amount", sa.Numeric(15, 2), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("rental_revenues")}
    if "pending_amount" in columns:
        op.drop_column("rental_revenues", "pending_amount")
