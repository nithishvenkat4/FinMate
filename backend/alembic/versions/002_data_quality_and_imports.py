"""002_data_quality_and_imports

Revision ID: 002_data_quality_and_imports
Revises: 001_initial_schema
Create Date: 2026-09-22 16:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_data_quality_and_imports'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create transaction_categories table
    op.create_table(
        'transaction_categories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category_type', sa.String(length=20), nullable=False, server_default='expense'),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transaction_categories_id'), 'transaction_categories', ['id'], unique=False)
    op.create_index(op.f('ix_transaction_categories_name'), 'transaction_categories', ['name'], unique=True)

    # 2. Create import_records table
    op.create_table(
        'import_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='csv_import'),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accepted_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rejected_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('warning_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duplicate_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='completed'),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_records_id'), 'import_records', ['id'], unique=False)
    op.create_index(op.f('ix_import_records_user_id'), 'import_records', ['user_id'], unique=False)

    # 3. Add Phase 2 columns to transactions table
    op.add_column('transactions', sa.Column('category_id', sa.Uuid(), nullable=True))
    op.add_column('transactions', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('transactions', sa.Column('source_type', sa.String(length=50), nullable=False, server_default='manual'))
    op.add_column('transactions', sa.Column('source_reference', sa.String(length=255), nullable=True))
    op.add_column('transactions', sa.Column('import_id', sa.Uuid(), nullable=True))
    op.add_column('transactions', sa.Column('data_quality_flags', sa.Text(), nullable=True))

    op.create_foreign_key('fk_transactions_category_id', 'transactions', 'transaction_categories', ['category_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_transactions_import_id', 'transactions', 'import_records', ['import_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_transactions_category_id'), 'transactions', ['category_id'], unique=False)
    op.create_index(op.f('ix_transactions_import_id'), 'transactions', ['import_id'], unique=False)
    op.create_index(op.f('ix_transactions_source_type'), 'transactions', ['source_type'], unique=False)
    op.create_index('ix_transactions_user_dedup', 'transactions', ['user_id', 'transaction_date', 'amount', 'description'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_transactions_user_dedup', table_name='transactions')
    op.drop_index(op.f('ix_transactions_source_type'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_import_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_category_id'), table_name='transactions')
    op.drop_constraint('fk_transactions_import_id', 'transactions', type_='foreignkey')
    op.drop_constraint('fk_transactions_category_id', 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'data_quality_flags')
    op.drop_column('transactions', 'import_id')
    op.drop_column('transactions', 'source_reference')
    op.drop_column('transactions', 'source_type')
    op.drop_column('transactions', 'notes')
    op.drop_column('transactions', 'category_id')
    op.drop_table('import_records')
    op.drop_table('transaction_categories')
