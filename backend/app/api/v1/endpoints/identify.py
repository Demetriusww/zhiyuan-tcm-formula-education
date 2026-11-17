# -*- coding: utf-8 -*-
"""药材图像识别 API：上传识别 + 识别历史"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.database_models import Herb, RecognitionRecord
from app.services.vision_service import HerbVisionService

router = APIRouter(tags=["药材识别"])


@router.post("")
async def identify(
    file: UploadFile = File(..., description="图片文件(jpg/png)，multipart 上传（ESP32 与网页均走此接口）"),
    source: str = Form("web", description="来源: web / esp32"),
    db: Session = Depends(get_db),
):
    """上传图片识别药材 → 返回识别结果并存入识别记录表"""
    svc = HerbVisionService(db)
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="图片内容为空")

    # 简易类型校验：jpg/png 文件头
    if not (image_bytes[:3] == b"\xff\xd8\xff" or image_bytes[:8] == b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG 图片")
    if len(image_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过 8MB")

    try:
        result = await svc.identify_image(image_bytes, source=source)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"识别服务调用失败: {e}")
    return {"code": 0, "message": "识别完成", "data": result}


@router.get("/records")
def records(source: str = None, limit: int = 50, db: Session = Depends(get_db)):
    """识别历史（可按来源 web/esp32 过滤）"""
    q = db.query(RecognitionRecord)
    if source:
        q = q.filter(RecognitionRecord.source == source)
    rows = q.order_by(RecognitionRecord.created_at.desc()).limit(min(limit, 200)).all()
    items = []
    for r in rows:
        herb = db.query(Herb).filter(Herb.id == r.herb_id).first() if r.herb_id else None
        items.append({
            "id": r.id,
            "source": r.source,
            "herb_name": r.herb_name,
            "matched": bool(r.matched),
            "herb_id": r.herb_id,
            "herb_detail": {
                "name": herb.name, "property": herb.property,
                "meridians": herb.meridians, "functions": herb.functions,
            } if herb else None,
            "raw_text": (r.raw_text or "")[:300],
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return {"code": 0, "message": "ok", "data": {"items": items, "total": len(items)}}
