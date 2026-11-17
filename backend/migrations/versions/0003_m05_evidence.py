# -*- coding: utf-8 -*-
"""M05 evidence library schema

* ancient_books: searchable evidence records used by the evidence page

The revision is additive and guarded, so applying it to the preserved database
does not modify existing business data.

Revision ID: 0003_m05_evidence
Revises: 0002_m01_m04_m06
Create Date: 2026-10-08
"""
import sqlalchemy as sa
from alembic import op

revision = "0003_m05_evidence"
down_revision = "0002_m01_m04_m06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "ancient_books" in inspector.get_table_names():
        return

    op.create_table(
        "ancient_books",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(100), nullable=False, index=True, unique=True),
        sa.Column("dynasty", sa.String(30), index=True),
        sa.Column("author", sa.String(100)),
        sa.Column("category", sa.String(30), index=True),
        sa.Column("description", sa.Text()),
        sa.Column("content", sa.Text()),
        sa.Column("prescriptions", sa.Text()),
        sa.Column("source_url", sa.String(500)),
        sa.Column("sort_order", sa.Integer(), server_default="0", index=True),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "ancient_books" in inspector.get_table_names():
        op.drop_table("ancient_books")
