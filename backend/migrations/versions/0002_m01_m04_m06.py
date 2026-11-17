# -*- coding: utf-8 -*-
"""M01/M04/M06 schema changes

* prescriptions: database level unique name + valid type default
* users: is_active flag for M06
* audit_logs: M06 operation audit
* efficacy_predictions: M04 persisted prediction records

Every step is guarded by an inspector check so the revision can be applied to
the preserved database without destroying data.

Revision ID: 0002_m01_m04_m06
Revises: 0001_baseline
Create Date: 2026-10-08
"""
import logging

import sqlalchemy as sa
from alembic import op

revision = "0002_m01_m04_m06"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

VALID_TYPES = ("经典名方", "现代方剂", "经验方", "自定义方剂")
TYPE_MAP = {
    "classic": "经典名方",
    "modern": "现代方剂",
    "experience": "经验方",
    "custom": "自定义方剂",
    "自拟方": "自定义方剂",
}


def _columns(inspector, table: str):
    return {c["name"] for c in inspector.get_columns(table)}


def _indexes(inspector, table: str):
    return {i["name"] for i in inspector.get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    # ---- M06: users.is_active ----
    if "users" in tables and "is_active" not in _columns(inspector, "users"):
        with op.batch_alter_table("users") as batch:
            batch.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))

    # ---- M01: normalise prescription types ----
    if "prescriptions" in tables:
        for old, new in TYPE_MAP.items():
            bind.execute(
                sa.text("UPDATE prescriptions SET type = :new WHERE type = :old"),
                {"new": new, "old": old},
            )
        bind.execute(
            sa.text(
                "UPDATE prescriptions SET type = '经典名方' "
                "WHERE type IS NULL OR type NOT IN :valid"
            ).bindparams(sa.bindparam("valid", expanding=True)),
            {"valid": list(VALID_TYPES)},
        )

        # ---- M01: unique prescription name (report duplicates instead of failing) ----
        inspector = sa.inspect(bind)
        dup_rows = bind.execute(
            sa.text(
                "SELECT trim(name) AS n, COUNT(*) AS c FROM prescriptions "
                "GROUP BY trim(name) HAVING COUNT(*) > 1"
            )
        ).fetchall()
        if dup_rows:
            for row in dup_rows:
                logger.warning(
                    "M01 迁移：方剂名称重复，未创建唯一约束 -> %s (%s 条)", row[0], row[1]
                )
        elif "uq_prescriptions_name" not in _indexes(inspector, "prescriptions"):
            op.create_index("uq_prescriptions_name", "prescriptions", ["name"], unique=True)

    # ---- M06: audit logs ----
    if "audit_logs" not in tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("operator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
            sa.Column("operator_name", sa.String(50), nullable=True),
            sa.Column("action", sa.String(50), nullable=False, index=True),
            sa.Column("target_type", sa.String(50), nullable=True),
            sa.Column("target_id", sa.String(50), nullable=True),
            sa.Column("detail", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), index=True),
        )

    # ---- M04: efficacy prediction records ----
    if "efficacy_predictions" not in tables:
        op.create_table(
            "efficacy_predictions",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("prescriptions.id"), nullable=False),
            sa.Column("target_symptoms", sa.Text(), nullable=True),
            sa.Column("predicted_efficacy", sa.Float(), nullable=True),
            sa.Column("confidence_level", sa.Float(), nullable=True),
            sa.Column("mechanism_analysis", sa.Text(), nullable=True),
            sa.Column("supporting_evidence", sa.Text(), nullable=True),
            sa.Column("contraindications", sa.Text(), nullable=True),
            sa.Column("risk_level", sa.String(10), server_default="low"),
            sa.Column("created_at", sa.DateTime(), index=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "efficacy_predictions" in tables:
        op.drop_table("efficacy_predictions")
    if "audit_logs" in tables:
        op.drop_table("audit_logs")
    if "prescriptions" in tables and "uq_prescriptions_name" in _indexes(inspector, "prescriptions"):
        op.drop_index("uq_prescriptions_name", table_name="prescriptions")
    if "users" in tables and "is_active" in _columns(inspector, "users"):
        with op.batch_alter_table("users") as batch:
            batch.drop_column("is_active")
