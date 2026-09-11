"""document intelligence metadata

Revision ID: 0004_intelligence
Revises: 0003_scope
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_intelligence"
down_revision = "0003_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("document_type", sa.String(length=20), nullable=False, server_default="pdf"))
    op.add_column("documents", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("author", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("processing_stage", sa.String(length=40), nullable=True))
    op.add_column("documents", sa.Column("intelligence", sa.Text(), nullable=True))
    op.add_column("document_chunks", sa.Column("heading", sa.String(length=255), nullable=True))
    op.add_column("document_chunks", sa.Column("section", sa.String(length=255), nullable=True))
    op.add_column("document_chunks", sa.Column("chunk_type", sa.String(length=20), nullable=False, server_default="text"))
    op.add_column("document_chunks", sa.Column("bbox", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("document_chunks", "bbox")
    op.drop_column("document_chunks", "chunk_type")
    op.drop_column("document_chunks", "section")
    op.drop_column("document_chunks", "heading")
    op.drop_column("documents", "intelligence")
    op.drop_column("documents", "processing_stage")
    op.drop_column("documents", "author")
    op.drop_column("documents", "title")
    op.drop_column("documents", "document_type")
