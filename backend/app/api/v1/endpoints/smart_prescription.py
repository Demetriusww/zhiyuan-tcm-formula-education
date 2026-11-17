"""
智能配伍 API 路由
输入症状 → 大模型生成 + N02 禁忌校验 → 返回候选方案（冲突标红用）
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import api_logger
from app.models.schemas import APIResponse
from app.services.smart_prescription_service import SmartPrescriptionService

router = APIRouter(tags=["智能配伍"])


class SmartRequest(BaseModel):
    symptoms: str = Field(..., min_length=2, max_length=1000, description="症状/体质描述")
    use_llm: bool = Field(default=True, description="是否优先使用大模型（false 时直接走本地知识库）")


@router.post("/compound", response_model=APIResponse, summary="智能配伍")
async def smart_compound(
    req: SmartRequest,
    db: Session = Depends(get_db),
):
    """
    智能配伍：输入症状/体质 → 生成配伍参考方案（2~3个），
    每个方案的药材均经过十八反/十九畏禁忌检测，冲突药材已标注。
    """
    try:
        service = SmartPrescriptionService(db)
        result = await service.generate(req.symptoms.strip(), use_llm=req.use_llm)
        api_logger.info(f"智能配伍完成: 方案数={len(result['candidates'])}, source={result.get('source')}")
        return APIResponse(code="SUCCESS", message="配伍方案生成完成", data=result)
    except Exception as e:
        api_logger.error(f"智能配伍失败: {e}")
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": f"智能配伍失败: {e}"})


@router.get("/health-check", response_model=APIResponse, summary="AI能力检测")
async def ai_health():
    """检测大模型是否可用（前端可据此显示提示）"""
    from app.core.config import settings
    available = bool(settings.LLM_API_KEY)
    return APIResponse(
        code="SUCCESS", message="OK",
        data={"llm_available": available, "model": settings.LLM_MODEL}
    )
