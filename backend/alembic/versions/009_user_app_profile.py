"""add users.app_profile for UI-only checklist role

Revision ID: 009_user_app_profile
Revises: 008_inventory_checklists
Create Date: 2026-10-29
"""

from alembic import op
import sqlalchemy as sa


revision = "009_user_app_profile"
down_revision = "008_inventory_checklists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "app_profile" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "app_profile",
                sa.String(length=20),
                nullable=False,
                server_default="full",
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "app_profile" in columns:
        op.drop_column("users", "app_profile")
