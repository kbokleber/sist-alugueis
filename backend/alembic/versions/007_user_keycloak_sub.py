"""add users.keycloak_sub and users.api_token

Revision ID: 007_user_keycloak
Revises: 006_platform_fee_pct
Create Date: 2026-10-29
"""

from alembic import op
import sqlalchemy as sa


revision = "007_user_keycloak"
down_revision = "006_platform_fee_pct"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}
    indexes = {index["name"] for index in inspector.get_indexes("users")}

    if "keycloak_sub" not in columns:
        op.add_column(
            "users",
            sa.Column("keycloak_sub", sa.String(length=64), nullable=True),
        )
    if "ix_users_keycloak_sub" not in indexes:
        op.create_index("ix_users_keycloak_sub", "users", ["keycloak_sub"], unique=True)

    if "api_token" not in columns:
        op.add_column(
            "users",
            sa.Column("api_token", sa.String(length=128), nullable=True),
        )
    if "ix_users_api_token" not in indexes:
        op.create_index("ix_users_api_token", "users", ["api_token"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}
    indexes = {index["name"] for index in inspector.get_indexes("users")}

    if "ix_users_api_token" in indexes:
        op.drop_index("ix_users_api_token", table_name="users")
    if "api_token" in columns:
        op.drop_column("users", "api_token")

    if "ix_users_keycloak_sub" in indexes:
        op.drop_index("ix_users_keycloak_sub", table_name="users")
    if "keycloak_sub" in columns:
        op.drop_column("users", "keycloak_sub")
