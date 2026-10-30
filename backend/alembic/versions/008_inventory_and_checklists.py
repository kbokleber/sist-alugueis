"""inventory categories, property inventory items and stay checklists

Revision ID: 008_inventory_checklists
Revises: 007_user_keycloak
Create Date: 2026-10-29
"""

from alembic import op
import sqlalchemy as sa


revision = "008_inventory_checklists"
down_revision = "007_user_keycloak"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_inventory_categories_user_name"),
    )
    op.create_index(
        "ix_inventory_categories_user_id",
        "inventory_categories",
        ["user_id"],
    )

    op.create_table(
        "property_inventory_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("quantity_expected", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["inventory_categories.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_property_inventory_items_property_id",
        "property_inventory_items",
        ["property_id"],
    )
    op.create_index(
        "ix_property_inventory_items_category_id",
        "property_inventory_items",
        ["category_id"],
    )
    op.create_index(
        "ix_property_inventory_items_property_category",
        "property_inventory_items",
        ["property_id", "category_id"],
    )

    checklist_type = sa.Enum("checkin", "checkout", name="checklist_type")
    checklist_status = sa.Enum("draft", "completed", name="checklist_status")
    checklist_item_condition = sa.Enum(
        "ok", "missing", "damaged", "other", name="checklist_item_condition"
    )
    checklist_type.create(op.get_bind(), checkfirst=True)
    checklist_status.create(op.get_bind(), checkfirst=True)
    checklist_item_condition.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "stay_checklists",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("rental_revenue_id", sa.Uuid(), nullable=False),
        sa.Column("checklist_type", checklist_type, nullable=False),
        sa.Column("status", checklist_status, nullable=False, server_default="draft"),
        sa.Column("performed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("performed_at", sa.DateTime(), nullable=True),
        sa.Column("general_notes", sa.Text(), nullable=True),
        sa.Column("has_incidents", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["performed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.ForeignKeyConstraint(["rental_revenue_id"], ["rental_revenues.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "rental_revenue_id",
            "checklist_type",
            name="uq_stay_checklists_revenue_type",
        ),
    )
    op.create_index("ix_stay_checklists_property_id", "stay_checklists", ["property_id"])
    op.create_index(
        "ix_stay_checklists_rental_revenue_id",
        "stay_checklists",
        ["rental_revenue_id"],
    )
    op.create_index(
        "ix_stay_checklists_performed_by_user_id",
        "stay_checklists",
        ["performed_by_user_id"],
    )

    op.create_table(
        "stay_checklist_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("checklist_id", sa.Uuid(), nullable=False),
        sa.Column("inventory_item_id", sa.Uuid(), nullable=True),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("category_name", sa.String(length=100), nullable=False),
        sa.Column("quantity_expected", sa.Integer(), nullable=False),
        sa.Column("quantity_found", sa.Integer(), nullable=True),
        sa.Column(
            "condition",
            checklist_item_condition,
            nullable=False,
            server_default="ok",
        ),
        sa.Column("incident_notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["checklist_id"],
            ["stay_checklists.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_item_id"],
            ["property_inventory_items.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_stay_checklist_items_checklist_id",
        "stay_checklist_items",
        ["checklist_id"],
    )
    op.create_index(
        "ix_stay_checklist_items_inventory_item_id",
        "stay_checklist_items",
        ["inventory_item_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_stay_checklist_items_inventory_item_id", table_name="stay_checklist_items")
    op.drop_index("ix_stay_checklist_items_checklist_id", table_name="stay_checklist_items")
    op.drop_table("stay_checklist_items")

    op.drop_index("ix_stay_checklists_performed_by_user_id", table_name="stay_checklists")
    op.drop_index("ix_stay_checklists_rental_revenue_id", table_name="stay_checklists")
    op.drop_index("ix_stay_checklists_property_id", table_name="stay_checklists")
    op.drop_table("stay_checklists")

    op.drop_index(
        "ix_property_inventory_items_property_category",
        table_name="property_inventory_items",
    )
    op.drop_index(
        "ix_property_inventory_items_category_id",
        table_name="property_inventory_items",
    )
    op.drop_index(
        "ix_property_inventory_items_property_id",
        table_name="property_inventory_items",
    )
    op.drop_table("property_inventory_items")

    op.drop_index("ix_inventory_categories_user_id", table_name="inventory_categories")
    op.drop_table("inventory_categories")

    sa.Enum(name="checklist_item_condition").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="checklist_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="checklist_type").drop(op.get_bind(), checkfirst=True)
