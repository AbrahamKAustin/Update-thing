"""New migration

Revision ID: c52308566716
Revises: 364d90d3ad2f
Create Date: 2025-02-01 06:48:54.436725

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c52308566716'
down_revision = '364d90d3ad2f'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('company_reference') as batch_op:
        batch_op.alter_column(
            'cik',
            existing_type=sa.INTEGER(),
            type_=sa.String(),
            existing_nullable=True,
            postgresql_using="cik::varchar"
        )

def downgrade() -> None:
    with op.batch_alter_table('company_reference') as batch_op:
        batch_op.alter_column(
            'cik',
            existing_type=sa.String(),
            type_=sa.INTEGER(),
            existing_nullable=True,
            postgresql_using="cik::integer"
        )