"""
模型模块
包含数据库ORM模型和Pydantic模型
"""
from app.models.database_models import (
    Herb,
    Prescription,
    PrescriptionHerb,
    AnalysisRecord,
    Conversation,
    User,
    Favorite,
    AuditLog,
    EfficacyPrediction,
    RecognitionRecord,
)
from app.models.schemas import (
    HerbBase,
    HerbCreate,
    HerbUpdate,
    HerbResponse,
    PrescriptionBase,
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse,
    PrescriptionHerb as PrescriptionHerbSchema,
    CompatibilityAnalysis,
    OptimizationResult,
    ComparisonResult,
    PaginationParams,
    PaginatedResponse,
    APIResponse,
    ErrorResponse
)

__all__ = [
    # 数据库模型
    "Herb",
    "Prescription",
    "PrescriptionHerb",
    "AnalysisRecord",
    "Conversation",
    "User",
    "Favorite",
    "AuditLog",
    "EfficacyPrediction",
    "RecognitionRecord",
    # Pydantic模型
    "HerbBase",
    "HerbCreate",
    "HerbUpdate",
    "HerbResponse",
    "PrescriptionBase",
    "PrescriptionCreate",
    "PrescriptionUpdate",
    "PrescriptionResponse",
    "PrescriptionHerbSchema",
    "CompatibilityAnalysis",
    "OptimizationResult",
    "ComparisonResult",
    "PaginationParams",
    "PaginatedResponse",
    "APIResponse",
    "ErrorResponse",
]
