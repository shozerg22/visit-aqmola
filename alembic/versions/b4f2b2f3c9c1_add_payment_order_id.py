"""add payment_order_id to bookings

Revision ID: b4f2b2f3c9c1
Revises: 1e290c38552b
Create Date: 2025-11-29
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b4f2b2f3c9c1'
down_revision = '1e290c38552b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('bookings', sa.Column('payment_order_id', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('bookings', 'payment_order_id')
