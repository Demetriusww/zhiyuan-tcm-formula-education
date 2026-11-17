# -*- coding: utf-8 -*-
"""baseline schema for the existing tcm_prescription database

This revision mirrors the schema that the preserved database already contains.
An existing database is stamped with this revision, while a brand new database
is built from it directly.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if "herbs" not in existing:
        op.create_table(
            "herbs",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(50), nullable=False, index=True),
            sa.Column("pinyin", sa.String(50)),
            sa.Column("property", sa.String(50)),
            sa.Column("flavor", sa.String(50)),
            sa.Column("meridians", sa.String(200)),
            sa.Column("latin", sa.String(100)),
            sa.Column("functions", sa.Text()),
            sa.Column("indications", sa.Text()),
            sa.Column("dosage", sa.String(100)),
            sa.Column("precautions", sa.String(500)),
            sa.Column("modern_research", sa.Text()),
            sa.Column("description", sa.Text()),
            sa.Column("category", sa.String(50), index=True),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )

    if "prescriptions" not in existing:
        op.create_table(
            "prescriptions",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(100), nullable=False, index=True),
            sa.Column("pinyin", sa.String(100)),
            sa.Column("description", sa.Text()),
            sa.Column("type", sa.String(20), server_default="经典名方"),
            sa.Column("source", sa.String(200)),
            sa.Column("indications", sa.Text()),
            sa.Column("functions", sa.Text()),
            sa.Column("usage", sa.Text()),
            sa.Column("precautions", sa.Text()),
            sa.Column("category", sa.String(50), index=True),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )

    if "prescription_herbs" not in existing:
        op.create_table(
            "prescription_herbs",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("prescriptions.id"), nullable=False),
            sa.Column("herb_id", sa.Integer(), sa.ForeignKey("herbs.id"), nullable=False),
            sa.Column("dosage", sa.String(50)),
            sa.Column("preparation", sa.String(100)),
            sa.Column("order", sa.Integer(), server_default="0"),
        )

    if "analysis_records" not in existing:
        op.create_table(
            "analysis_records",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("prescriptions.id")),
            sa.Column("analysis_type", sa.String(20), nullable=False),
            sa.Column("input_data", sa.Text()),
            sa.Column("result_data", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        )

    if "conversations" not in existing:
        op.create_table(
            "conversations",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("session_id", sa.String(100), nullable=False, index=True),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime()),
        )

    if "users" not in existing:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("username", sa.String(50), nullable=False, unique=True, index=True),
            sa.Column("password_hash", sa.String(200), nullable=False),
            sa.Column("nickname", sa.String(50)),
            sa.Column("email", sa.String(100)),
            sa.Column("role", sa.String(20), server_default="user"),
            sa.Column("created_at", sa.DateTime()),
        )

    if "favorites" not in existing:
        op.create_table(
            "favorites",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("prescriptions.id"), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime()),
            sa.UniqueConstraint("user_id", "prescription_id", name="uq_user_prescription"),
        )

    if "recognition_records" not in existing:
        op.create_table(
            "recognition_records",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("source", sa.String(20), server_default="web"),
            sa.Column("image_path", sa.String(300)),
            sa.Column("raw_text", sa.Text()),
            sa.Column("herb_name", sa.String(100), index=True),
            sa.Column("herb_id", sa.Integer(), sa.ForeignKey("herbs.id")),
            sa.Column("matched", sa.Integer(), server_default="0"),
            sa.Column("created_at", sa.DateTime()),
        )


def downgrade() -> None:
    for table in (
        "recognition_records",
        "favorites",
        "users",
        "conversations",
        "analysis_records",
        "prescription_herbs",
        "prescriptions",
        "herbs",
    ):
        op.drop_table(table)
