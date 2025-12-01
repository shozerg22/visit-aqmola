"""add user role column

Revision ID: add_user_role
Revises: b4f2b2f3c9c1  # previous migration id placeholder
Create Date: 2025-11-29
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_user_role'
down_revision = 'b4f2b2f3c9c1'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('role', sa.String(length=50), nullable=False, server_default='user'))


def downgrade():
    op.drop_column('users', 'role')
