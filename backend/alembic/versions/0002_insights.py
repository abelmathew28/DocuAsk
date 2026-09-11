"""add document insights columns

Revision ID: 0002_insights
Revises: 0001_initial
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_insights"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("is_starred", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("documents", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("suggested_questions", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "suggested_questions")
    op.drop_column("documents", "summary")
    op.drop_column("documents", "is_starred")
