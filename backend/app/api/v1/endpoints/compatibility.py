"""
配伍禁忌检测 API 路由
接收药材列表 → 返回十八反/十九畏冲突检测结果（纯规则算法）
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.algorithm.compatibility_checker import checker
from app.models.schemas import APIResponse

router = APIRouter(tags=["配伍禁忌"])


class CompatibilityRequest(BaseModel):
    """检测请求"""
    herbs: List[str] = Field(..., min_length=1, description="药材名称列表")
    source: Optional[str] = Field(None, description="来源说明（如：AI生成/手动输入/方剂ID）")


@router.post("/check", response_model=APIResponse, summary="配伍禁忌检测")
async def check_compatibility(req: CompatibilityRequest):
    """
    配伍禁忌检测：对给定药材列表执行十八反、十九畏规则检测。

    - 纯确定性规则算法（不调用大模型）
    - 支持炮制/别名（如"姜半夏"、"制附子"）
    """
    try:
        herbs = [h.strip() for h in req.herbs if h and h.strip()]
        if not herbs:
            raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR", "message": "药材列表不能为空"})
        result = checker.check_with_summary(herbs)
        result["source"] = req.source
        return APIResponse(code="SUCCESS", message="检测完成", data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(e)})


@router.get("/rules/summary", response_model=APIResponse, summary="规则概览")
async def rules_summary():
    """返回规则体系概览（供文档/前端展示）"""
    from app.services.algorithm.conflict_rules import EIGHTEEN_OPPOSITES, NINETEEN_FEARS, RULE_CATALOG
    return APIResponse(
        code="SUCCESS",
        message="获取成功",
        data={
            "rule_catalog": RULE_CATALOG,
            "eighteen_opposites": [
                {"name": g["group_name"], "members": g["members"], "opposes": g["opposes"],
                 "description": g["description"], "tip": g["tip"]}
                for g in EIGHTEEN_OPPOSITES
            ],
            "nineteen_fears": NINETEEN_FEARS,
        }
    )
