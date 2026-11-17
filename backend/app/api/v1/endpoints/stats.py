# -*- coding: utf-8 -*-
"""平台统计与知识图谱 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.stats_service import StatsService

router = APIRouter(tags=["统计分析"])


def _service(db: Session = Depends(get_db)) -> StatsService:
    return StatsService(db)


@router.get("/overview")
def overview(service: StatsService = Depends(_service)):
    """平台统计总览：药材频次 / 方剂分类 / 药性 / 归经 / 药味分布"""
    return {"code": 0, "message": "ok", "data": service.overview()}


@router.get("/graph")
def graph(
    mode: str = Query("all", description="all=全量 / top=高频药材 / category=按分类"),
    category: Optional[str] = Query(None, description="mode=category 时的方剂分类名"),
    top_n: int = Query(30, ge=10, le=80, description="mode=top 时的药材数量"),
    service: StatsService = Depends(_service),
):
    """药材-方剂力导向图节点/边数据"""
    return {"code": 0, "message": "ok", "data": service.graph(mode=mode, category=category, top_n=top_n)}
