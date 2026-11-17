# -*- coding: utf-8 -*-
"""用户收藏 API：收藏 / 取消 / 列表 / 已收藏 ID 集合"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_current_user
from app.models.database_models import Favorite, Prescription, PrescriptionHerb, User
from app.models.schemas import APIResponse

router = APIRouter(tags=["方剂收藏"])


def _prescription_brief(p: Prescription) -> dict:
    """方剂简要信息（含组成药材名列表）"""
    herb_names = [
        item.herb.name
        for item in sorted(p.herbs or [], key=lambda row: row.order or 0)
        if item.herb
    ]
    return {
        "id": p.id, "name": p.name, "pinyin": p.pinyin,
        "category": p.category, "source": p.source,
        "functions": p.functions, "indications": p.indications,
        "herb_count": len(herb_names),
        "herb_names": herb_names,
    }


@router.get("")
def my_favorites(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我的收藏：返回方剂完整列表（按收藏时间倒序）"""
    rows = (
        db.query(Favorite)
        .options(
            joinedload(Favorite.prescription)
            .joinedload(Prescription.herbs)
            .joinedload(PrescriptionHerb.herb)
        )
        .join(Prescription, Favorite.prescription_id == Prescription.id)
        .filter(Favorite.user_id == current.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    items = [_prescription_brief(row.prescription) for row in rows]
    return APIResponse(
        message="获取成功",
        data={"items": items, "total": len(items)},
    )


@router.get("/ids")
def my_favorite_ids(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我收藏的方剂 ID 集合（供前端标注星标状态）"""
    ids = [
        f.prescription_id for f in db.query(Favorite)
        .filter(Favorite.user_id == current.id).all()
    ]
    return APIResponse(message="获取成功", data={"ids": ids})


@router.post("/{prescription_id}")
def add_favorite(
    prescription_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """收藏方剂（幂等：重复收藏不报错）"""
    p = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not p:
        raise NotFoundError("方剂不存在")
    exists = db.query(Favorite).filter(
        Favorite.user_id == current.id,
        Favorite.prescription_id == prescription_id,
    ).first()
    if not exists:
        db.add(Favorite(user_id=current.id, prescription_id=prescription_id))
        db.commit()
    return APIResponse(message="收藏成功", data={"favorited": True})


@router.delete("/{prescription_id}")
def remove_favorite(
    prescription_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取消收藏（幂等）"""
    fav = db.query(Favorite).filter(
        Favorite.user_id == current.id,
        Favorite.prescription_id == prescription_id,
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
    return APIResponse(message="已取消收藏", data={"favorited": False})
