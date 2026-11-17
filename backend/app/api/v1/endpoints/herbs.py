"""
药材API路由
提供药材的查询、管理接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.database_models import Herb
from app.models.schemas import APIResponse

router = APIRouter(tags=["药材管理"])


def _herb_dict(h: Herb) -> dict:
    """将 ORM 对象转为 dict（避免 schema 枚举校验与自由文本冲突）"""
    return {
        "id": h.id,
        "name": h.name,
        "pinyin": h.pinyin,
        "property": h.property,
        "flavor": h.flavor,
        "meridians": h.meridians,
        "latin": h.latin,
        "functions": h.functions,
        "indications": h.indications,
        "dosage": h.dosage,
        "precautions": h.precautions,
        "modern_research": h.modern_research,
        "description": h.description,
        "category": h.category,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }


@router.get("", response_model=APIResponse, summary="获取药材列表")
async def list_herbs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    name: Optional[str] = Query(None, description="按名称精确匹配"),
    keyword: Optional[str] = Query(None, description="关键词模糊搜索"),
    category: Optional[str] = Query(None, description="分类筛选"),
    db: Session = Depends(get_db),
):
    """获取药材列表，支持名称/关键词/分类筛选"""
    try:
        query = db.query(Herb)
        if name:
            query = query.filter(Herb.name == name)
        if category:
            query = query.filter(Herb.category == category)
        if keyword:
            query = query.filter(
                Herb.name.contains(keyword) | Herb.functions.contains(keyword)
            )

        total = query.count()
        herbs = query.order_by(Herb.id).offset((page - 1) * page_size).limit(page_size).all()

        return APIResponse(
            code="SUCCESS", message="获取成功",
            data={"items": [_herb_dict(h) for h in herbs], "total": total,
                  "page": page, "page_size": page_size}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "DATABASE_ERROR", "message": str(e)})


@router.get("/all-names", response_model=APIResponse, summary="获取全部药材名->ID映射")
async def all_herb_names(db: Session = Depends(get_db)):
    """获取全部药材的 (id, name)，用于前端把药名解析为 herb_id"""
    try:
        herbs = db.query(Herb.id, Herb.name).all()
        return APIResponse(
            code="SUCCESS", message="获取成功",
            data={"items": [{"id": h.id, "name": h.name} for h in herbs],
                  "total": len(herbs)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "DATABASE_ERROR", "message": str(e)})


@router.get("/{herb_id}", response_model=APIResponse, summary="获取药材详情")
async def get_herb(herb_id: int, db: Session = Depends(get_db)):
    """获取单味药材详情"""
    herb = db.query(Herb).filter(Herb.id == herb_id).first()
    if not herb:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "药材不存在"})
    return APIResponse(code="SUCCESS", message="获取成功", data=_herb_dict(herb))
