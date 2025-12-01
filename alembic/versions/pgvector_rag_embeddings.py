"""create rag_embeddings table with pgvector

Revision ID: pgvector_rag_embeddings
Revises: add_user_role
Create Date: 2025-11-29
"""
from alembic import op
import sqlalchemy as sa
from config import settings

try:
    from pgvector.sqlalchemy import Vector
except Exception:
    Vector = None  # type: ignore

# revision identifiers, used by Alembic.
revision = 'pgvector_rag_embeddings'
down_revision = 'add_user_role'
branch_labels = None
depends_on = None

def upgrade():
    # Ensure extension exists (PostgreSQL)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    cols = [
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('doc_id', sa.String(length=32), nullable=False, unique=True),
        sa.Column('title', sa.String(length=300), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    ]
    if Vector is not None:
        cols.append(sa.Column('embedding', Vector(settings.PGVECTOR_DIM)))
    else:
        cols.append(sa.Column('embedding', sa.Text(), nullable=True))
    op.create_table('rag_embeddings', *cols)
    op.create_index('ix_rag_embeddings_doc_id', 'rag_embeddings', ['doc_id'])

def downgrade():
    op.drop_index('ix_rag_embeddings_doc_id', table_name='rag_embeddings')
    op.drop_table('rag_embeddings')
