"""003_agent_orchestration

Revision ID: 003_agent_orchestration
Revises: 002_data_quality_and_imports
Create Date: 2026-09-22 21:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_agent_orchestration'
down_revision: Union[str, None] = '002_data_quality_and_imports'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create agent_tasks table
    op.create_table(
        'agent_tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=100), nullable=False, server_default='UNKNOWN'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('facts', sa.JSON(), nullable=False),
        sa.Column('predictions', sa.JSON(), nullable=False),
        sa.Column('recommendations', sa.JSON(), nullable=False),
        sa.Column('tradeoffs', sa.JSON(), nullable=False),
        sa.Column('assumptions', sa.JSON(), nullable=False),
        sa.Column('uncertainties', sa.JSON(), nullable=False),
        sa.Column('sources', sa.JSON(), nullable=False),
        sa.Column('execution_trace', sa.JSON(), nullable=False),
        sa.Column('agents_used', sa.JSON(), nullable=False),
        sa.Column('tools_used', sa.JSON(), nullable=False),
        sa.Column('disagreements', sa.JSON(), nullable=False),
        sa.Column('evidence_quality', sa.String(length=50), nullable=False, server_default='HIGH_EVIDENCE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_tasks_id'), 'agent_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_agent_tasks_user_id'), 'agent_tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_agent_tasks_intent'), 'agent_tasks', ['intent'], unique=False)
    op.create_index(op.f('ix_agent_tasks_status'), 'agent_tasks', ['status'], unique=False)

    # 2. Create agent_approvals table
    op.create_table(
        'agent_approvals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('target_id', sa.String(length=100), nullable=False),
        sa.Column('current_value', sa.JSON(), nullable=False),
        sa.Column('proposed_value', sa.JSON(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['agent_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_approvals_id'), 'agent_approvals', ['id'], unique=False)
    op.create_index(op.f('ix_agent_approvals_task_id'), 'agent_approvals', ['task_id'], unique=False)
    op.create_index(op.f('ix_agent_approvals_user_id'), 'agent_approvals', ['user_id'], unique=False)
    op.create_index(op.f('ix_agent_approvals_status'), 'agent_approvals', ['status'], unique=False)

    # 3. Create agent_tool_calls table
    op.create_table(
        'agent_tool_calls',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('is_mutation', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['agent_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_tool_calls_id'), 'agent_tool_calls', ['id'], unique=False)
    op.create_index(op.f('ix_agent_tool_calls_task_id'), 'agent_tool_calls', ['task_id'], unique=False)
    op.create_index(op.f('ix_agent_tool_calls_agent_name'), 'agent_tool_calls', ['agent_name'], unique=False)
    op.create_index(op.f('ix_agent_tool_calls_tool_name'), 'agent_tool_calls', ['tool_name'], unique=False)


def downgrade() -> None:
    op.drop_table('agent_tool_calls')
    op.drop_table('agent_approvals')
    op.drop_table('agent_tasks')
