"""M02 标准智能方剂推荐接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import APIResponse, RecommendationRequest
from app.services.smart_prescription_service import SmartPrescriptionService

router = APIRouter(tags=["智能推荐"])


@router.post("", response_model=APIResponse, summary="智能方剂推荐")
async def recommend_prescriptions(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
):
    service = SmartPrescriptionService(db)
    result = await service.generate_recommendations(
        request.symptoms,
        constraints=request.constraints,
        use_llm=request.use_llm,
    )
    message = "推荐完成" if result.recommendations else "未找到明确匹配方剂"
    return APIResponse(message=message, data=result)
