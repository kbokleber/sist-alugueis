"""initial migration

Revision ID: 001_initial
Revises:
Create Date: 2026-04-05

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid, primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_superuser', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )

    # Create properties table
    op.create_table(
        'properties',
        sa.Column('id', sa.Uuid, primary_key=True),
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('property_value', sa.Numeric(15, 2), nullable=False),
        sa.Column('monthly_depreciation_percent', sa.Numeric(5, 2), default=1.00),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )

    # Create financial_categories table
    op.create_table(
        'financial_categories',
        sa.Column('id', sa.Uuid, primary_key=True),
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.Enum('REVENUE', 'EXPENSE', name='categorytype'), nullable=False),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create rental_revenues table
    op.create_table(
        'rental_revenues',
        sa.Column('id', sa.Uuid, primary_key=True),
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('property_id', sa.Uuid, sa.ForeignKey('properties.id'), nullable=False, index=True),
        sa.Column('year_month', sa.String(7), nullable=False, index=True),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('checkin_date', sa.Date, nullable=True),
        sa.Column('checkout_date', sa.Date, nullable=True),
        sa.Column('guest_name', sa.String(255), nullable=False),
        sa.Column('listing_name', sa.String(255), nullable=True),
        sa.Column('listing_source', sa.String(50), nullable=True),
        sa.Column('nights', sa.Integer, nullable=False),
        sa.Column('gross_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('cleaning_fee', sa.Numeric(15, 2), default=0),
        sa.Column('platform_fee', sa.Numeric(15, 2), default=0),
        sa.Column('net_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )
    op.create_index('idx_revenues_property_month', 'rental_revenues', ['property_id', 'year_month'])
    op.create_index('idx_revenues_user_month', 'rental_revenues', ['user_id', 'year_month'])
    op.create_index('idx_revenues_guest', 'rental_revenues', ['guest_name'])

    # Create property_expenses table
    op.create_table(
        'property_expenses',
        sa.Column('id', sa.Uuid, primary_key=True),
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('property_id', sa.Uuid, sa.ForeignKey('properties.id'), nullable=False, index=True),
        sa.Column('category_id', sa.Uuid, sa.ForeignKey('financial_categories.id'), nullable=False, index=True),
        sa.Column('year_month', sa.String(7), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('is_reserve', sa.Boolean, default=False),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('paid_date', sa.Date, nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PAID', 'CANCELLED', name='expensestatus'), default='PENDING'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )
    op.create_index('idx_expenses_property_month', 'property_expenses', ['property_id', 'year_month'])
    op.create_index('idx_expenses_category', 'property_expenses', ['category_id'])

    # Create monthly_closings table
    op.create_table(
        'monthly_closings',
        sa.Column('id', sa.Uuid, primary_key=True),
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('property_id', sa.Uuid, sa.ForeignKey('properties.id'), nullable=False),
        sa.Column('year_month', sa.String(7), nullable=False),
        sa.Column('total_revenue', sa.Numeric(15, 2), nullable=False, default=0),
        sa.Column('total_expenses', sa.Numeric(15, 2), nullable=False, default=0),
        sa.Column('net_result', sa.Numeric(15, 2), nullable=False, default=0),
        sa.Column('total_nights', sa.Integer, default=0),
        sa.Column('total_bookings', sa.Integer, default=0),
        sa.Column('depreciation_value', sa.Numeric(15, 2), default=0),
        sa.Column('cleaning_total', sa.Numeric(15, 2), default=0),
        sa.Column('platform_fee_total', sa.Numeric(15, 2), default=0),
        sa.Column('other_expenses', sa.Numeric(15, 2), default=0),
        sa.Column('status', sa.Enum('OPEN', 'CLOSED', name='closingstatus'), default='OPEN'),
        sa.Column('closed_at', sa.DateTime, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )
    op.create_index('idx_closing_property_month', 'monthly_closings', ['property_id', 'year_month'], unique=True)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid, primary_key=True),
        sa.Column('user_id', sa.Uuid, sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.Uuid, nullable=False),
        sa.Column('old_values', sa.JSON, nullable=True),
        sa.Column('new_values', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_user_date', 'audit_logs', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('monthly_closings')
    op.drop_table('property_expenses')
    op.drop_index('idx_revenues_guest', 'rental_revenues')
    op.drop_index('idx_revenues_user_month', 'rental_revenues')
    op.drop_index('idx_revenues_property_month', 'rental_revenues')
    op.drop_table('rental_revenues')
    op.drop_table('financial_categories')
    op.drop_table('properties')
    op.drop_table('users')
