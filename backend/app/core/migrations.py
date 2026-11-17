# -*- coding: utf-8 -*-
"""数据库结构升级入口。

启动时由 ``ensure_database_schema()`` 调用 Alembic 把数据库升到最新版本：

1. 全新数据库：从 baseline 迁移开始建表。
2. 已存在的历史数据库（没有 alembic_version 表）：先把当前结构标记为
   baseline，再增量执行后续迁移，因此不会重建、不会清空已有数据。
3. 迁移前会检查方剂名称重复情况，发现重名时输出报告并保留数据。
"""
from pathlib import Path
from typing import List, Tuple

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.core.config import settings
from app.core.database import engine
from app.core.logger import db_logger

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
BASELINE_REVISION = "0001_baseline"
HEAD_REVISION = "0003_m05_evidence"


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg


def _schema_state() -> Tuple[bool, bool]:
    """返回 (是否已有 alembic_version, 是否已有核心业务表)"""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    has_version = "alembic_version" in table_names
    has_core = {"prescriptions", "users", "herbs"}.issubset(table_names)
    return has_version, has_core


def find_duplicate_prescription_names() -> List[Tuple[str, int]]:
    """返回去除首尾空白后重名的方剂名称及数量（用于迁移前报告）"""
    inspector = inspect(engine)
    if "prescriptions" not in inspector.get_table_names():
        return []
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT trim(name) AS n, COUNT(*) AS c FROM prescriptions "
                "GROUP BY trim(name) HAVING COUNT(*) > 1 ORDER BY c DESC"
            )
        ).fetchall()
    return [(row[0], row[1]) for row in rows]


def ensure_database_schema() -> dict:
    """把数据库结构升级到最新版本，返回执行摘要。"""
    duplicates = find_duplicate_prescription_names()
    if duplicates:
        db_logger.warning(
            "检测到重名方剂，唯一约束将暂不创建："
            + "；".join(f"{name} x{count}" for name, count in duplicates)
        )

    has_version, has_core = _schema_state()
    cfg = _alembic_config()

    if not has_version and has_core:
        command.stamp(cfg, BASELINE_REVISION)
        db_logger.info("检测到已有数据库，已标记为 baseline 迁移版本")

    command.upgrade(cfg, "head")
    db_logger.info("数据库结构迁移完成（head=%s）", HEAD_REVISION)

    return {
        "revision": HEAD_REVISION,
        "stamped_baseline": (not has_version and has_core),
        "duplicates": duplicates,
    }
