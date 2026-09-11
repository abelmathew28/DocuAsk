"""conversation scope and citation document ids

Revision ID: 0003_scope
Revises: 0002_insights
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_scope"
down_revision = "0002_insights"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conversations", sa.Column("scope", sa.String(length=20), nullable=False, server_default="document"))
    op.add_column("conversations", sa.Column("document_ids", sa.Text(), nullable=True))
    op.add_column("message_sources", sa.Column("document_id", sa.String(length=36), nullable=True))


def downgrade() -> None:
    op.drop_column("message_sources", "document_id")
    op.drop_column("conversations", "document_ids")
    op.drop_column("conversations", "scope")
