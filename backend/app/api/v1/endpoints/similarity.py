# -*- coding: utf-8 -*-
"""方剂相似度 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.algorithm.prescription_similarity import PrescriptionSimilarityService

router = APIRouter(tags=["方剂相似度"])


def _service(db: Session = Depends(get_db)) -> PrescriptionSimilarityService:
    return PrescriptionSimilarityService(db)


@router.get("")
def similar_prescriptions(
    name: str = Query(None, description="方剂名称"),
    prescription_id: int = Query(None, description="方剂ID(与name二选一)"),
    top_k: int = Query(5, ge=1, le=10, description="返回相似方剂数量"),
    min_overlap: int = Query(0, ge=0, description="最少共用药味数过滤(0=不过滤)"),
    service: PrescriptionSimilarityService = Depends(_service),
):
    """
    查询与指定方剂最相似的 TopN 方剂（含雷达图所需的性味归经指纹数据）
    """
    if not name and not prescription_id:
        raise HTTPException(status_code=422, detail="必须提供 name 或 prescription_id")
    result = service.similar(name=name, prescription_id=prescription_id,
                             top_k=top_k, min_overlap=min_overlap)
    if result is None:
        raise HTTPException(status_code=404, detail=f"方剂不存在: {name or prescription_id}")
    return {"code": 0, "message": "ok", "data": result}
