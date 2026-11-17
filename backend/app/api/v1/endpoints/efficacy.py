"""M04 药效预测 API 路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.database_models import User
from app.models.schemas import (
    APIResponse,
    EfficacyPredictionRequest,
    EfficacyPredictionResponse,
)
from app.services.efficacy_service import EfficacyService

router = APIRouter(tags=["药效预测"])


def get_efficacy_service(db: Session = Depends(get_db)) -> EfficacyService:
    return EfficacyService(db)


@router.post(
    "/predict",
    response_model=APIResponse,
    summary="预测方剂对目标症状的疗效",
)
async def predict_efficacy(
    request: EfficacyPredictionRequest,
    current_user: User = Depends(get_current_user),
    service: EfficacyService = Depends(get_efficacy_service),
):
    result: EfficacyPredictionResponse = await service.predict(
        prescription_id=request.prescription_id,
        target_symptoms=request.target_symptoms,
        user_id=current_user.id,
    )
    return APIResponse(message="疗效预测完成", data=result)
