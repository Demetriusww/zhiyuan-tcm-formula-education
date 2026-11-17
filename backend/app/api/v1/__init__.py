"""
API V1版本路由
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    chat,
    compatibility,
    efficacy,
    evidence,
    favorites,
    herbs,
    identify,
    prescriptions,
    recommendations,
    similarity,
    smart_prescription,
    stats,
)

api_router = APIRouter()

# 方剂相关路由
api_router.include_router(
    prescriptions.router,
    prefix="/prescriptions",
    tags=["方剂管理"]
)

# 药材路由
api_router.include_router(
    herbs.router,
    prefix="/herbs",
    tags=["药材管理"]
)

# 配伍禁忌路由
api_router.include_router(
    compatibility.router,
    prefix="/compatibility",
    tags=["配伍禁忌"]
)

# 智能配伍路由
api_router.include_router(
    smart_prescription.router,
    prefix="/smart",
    tags=["智能配伍"]
)

# M02 标准智能推荐路由
api_router.include_router(
    recommendations.router,
    prefix="/recommendations",
    tags=["智能推荐"]
)

# M04 药效预测路由
api_router.include_router(
    efficacy.router,
    prefix="/efficacy",
    tags=["药效预测"]
)

# M06 系统管理路由
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["系统管理"]
)

# 方剂相似度路由
api_router.include_router(
    similarity.router,
    prefix="/similarity",
    tags=["方剂相似度"]
)

# 统计分析路由
api_router.include_router(
    stats.router,
    prefix="/stats",
    tags=["统计分析"]
)

# 用户认证路由
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["用户认证"]
)

# 方剂收藏路由
api_router.include_router(
    favorites.router,
    prefix="/favorites",
    tags=["方剂收藏"]
)

# 药材识别路由
api_router.include_router(
    identify.router,
    prefix="/identify",
    tags=["药材识别"]
)

# 聊天对话路由
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["方剂科普问答"]
)

# M05 古籍文献路由
api_router.include_router(
    evidence.router,
    prefix="/evidence",
    tags=["古籍文献"],
)
