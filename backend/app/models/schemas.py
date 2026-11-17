"""
数据模型定义
包含所有Pydantic模型和枚举类型
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from enum import Enum
from pydantic import BaseModel, Field, validator


class TCMProperty(str, Enum):
    """中药药性枚举"""
    COLD = "寒"
    COOL = "凉"
    WARM = "温"
    HOT = "热"
    NEUTRAL = "平"


class TCMFlavor(str, Enum):
    """中药五味枚举"""
    SOUR = "酸"
    BITTER = "苦"
    SWEET = "甘"
    PUNGENT = "辛"
    SALTY = "咸"


class Meridian(str, Enum):
    """经络枚举"""
    LUNG = "肺经"
    LARGE_INTESTINE = "大肠经"
    STOMACH = "胃经"
    SPLEEN = "脾经"
    HEART = "心经"
    SMALL_INTESTINE = "小肠经"
    BLADDER = "膀胱经"
    KIDNEY = "肾经"
    PERICARDIUM = "心包经"
    SANJIAO = "三焦经"
    GALLBLADDER = "胆经"
    LIVER = "肝经"


class PrescriptionType(str, Enum):
    """方剂类型枚举"""
    CLASSIC = "经典名方"
    MODERN = "现代方剂"
    EXPERIENCE = "经验方"
    CUSTOM = "自定义方剂"


class AnalysisType(str, Enum):
    """分析类型枚举"""
    COMPATIBILITY = "配伍分析"
    OPTIMIZATION = "优化设计"
    COMPARISON = "对比评估"


class HerbBase(BaseModel):
    """中药基础模型"""
    name: str = Field(..., min_length=1, max_length=50, description="中药名称")
    pinyin: Optional[str] = Field(None, max_length=50, description="拼音")
    property: Optional[TCMProperty] = Field(None, description="药性")
    flavor: Optional[List[TCMFlavor]] = Field(default_factory=list, description="药味")
    meridians: Optional[List[Meridian]] = Field(default_factory=list, description="归经")
    functions: Optional[str] = Field(None, max_length=1000, description="功效")
    indications: Optional[str] = Field(None, max_length=1000, description="主治")
    dosage: Optional[str] = Field(None, max_length=100, description="常用剂量")
    precautions: Optional[str] = Field(None, max_length=500, description="禁忌")


class HerbCreate(HerbBase):
    """创建中药模型"""
    pass


class HerbUpdate(BaseModel):
    """更新中药模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    pinyin: Optional[str] = Field(None, max_length=50)
    property: Optional[TCMProperty] = None
    flavor: Optional[List[TCMFlavor]] = None
    meridians: Optional[List[Meridian]] = None
    functions: Optional[str] = Field(None, max_length=1000)
    indications: Optional[str] = Field(None, max_length=1000)
    dosage: Optional[str] = Field(None, max_length=100)
    precautions: Optional[str] = Field(None, max_length=500)


class HerbResponse(HerbBase):
    """中药响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PrescriptionHerb(BaseModel):
    """方剂中的中药模型"""
    herb_id: int = Field(..., description="中药ID")
    name: str = Field(..., description="中药名称")
    dosage: str = Field(..., max_length=50, description="剂量")
    preparation: Optional[str] = Field(None, max_length=100, description="炮制方法")
    order: int = Field(default=0, description="顺序")


class PrescriptionBase(BaseModel):
    """方剂基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="方剂名称")
    pinyin: Optional[str] = Field(None, max_length=100, description="拼音")
    type: PrescriptionType = Field(default=PrescriptionType.CLASSIC, description="方剂类型")
    source: Optional[str] = Field(None, max_length=200, description="来源")
    functions: Optional[str] = Field(None, max_length=1000, description="功效")
    indications: Optional[str] = Field(None, max_length=2000, description="主治")
    usage: Optional[str] = Field(None, max_length=500, description="用法")
    precautions: Optional[str] = Field(None, max_length=500, description="禁忌")
    category: Optional[str] = Field(None, max_length=50, description="方剂分类：解表剂/补益剂等")


class PrescriptionCreate(PrescriptionBase):
    """创建方剂模型"""
    herbs: List[PrescriptionHerb] = Field(..., min_items=2, max_items=30, description="组成药物")

    @validator('herbs')
    def validate_herbs(cls, v):
        if len(v) < 2:
            raise ValueError('方剂至少包含2味药物')
        if len(v) > 30:
            raise ValueError('方剂最多包含30味药物')
        return v


class PrescriptionUpdate(BaseModel):
    """更新方剂模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    pinyin: Optional[str] = Field(None, max_length=100)
    type: Optional[PrescriptionType] = None
    source: Optional[str] = Field(None, max_length=200)
    functions: Optional[str] = Field(None, max_length=1000)
    indications: Optional[str] = Field(None, max_length=2000)
    usage: Optional[str] = Field(None, max_length=500)
    precautions: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50, description="方剂分类：解表剂/补益剂等")
    herbs: Optional[List[PrescriptionHerb]] = None

    @validator('herbs')
    def validate_herbs(cls, v):
        if v is None:
            return v
        if len(v) < 2:
            raise ValueError('方剂至少包含2味药物')
        if len(v) > 30:
            raise ValueError('方剂最多包含30味药物')
        return v


class PrescriptionResponse(PrescriptionBase):
    """方剂响应模型"""
    id: int
    type: str = Field(default="经典名方", description="方剂类型")
    herbs: List[PrescriptionHerb]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PrescriptionCompareRequest(BaseModel):
    """方剂对比请求"""
    prescription_ids: List[int] = Field(..., min_items=2, max_items=5)


class PrescriptionOptimizeRequest(BaseModel):
    """方剂优化请求"""
    target_symptoms: List[str] = Field(default_factory=list, max_items=20)


class ImportRowError(BaseModel):
    """批量导入单行错误"""
    row: int
    name: Optional[str] = None
    code: str
    message: str


class ImportResult(BaseModel):
    """批量导入统计"""
    total: int = 0
    created: int = 0
    skipped: int = 0
    failed: int = 0
    errors: List[ImportRowError] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    """分析请求模型"""
    input_type: str = Field(..., description="输入类型: symptom/prescription/herbs")
    content: str = Field(..., min_length=1, max_length=1000, description="输入内容")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="分析选项")

    @validator('input_type')
    def validate_input_type(cls, v):
        allowed = ['symptom', 'prescription', 'herbs']
        if v not in allowed:
            raise ValueError(f'input_type必须是以下之一: {allowed}')
        return v


class CompatibilityAnalysis(BaseModel):
    """配伍分析结果"""
    prescription_name: str = Field(..., description="方剂名称")
    overall_score: float = Field(..., ge=0, le=100, description="综合评分")
    monarch_herb: Optional[PrescriptionHerb] = Field(None, description="君药")
    minister_herbs: List[PrescriptionHerb] = Field(default_factory=list, description="臣药")
    assistant_herbs: List[PrescriptionHerb] = Field(default_factory=list, description="佐药")
    messenger_herbs: List[PrescriptionHerb] = Field(default_factory=list, description="使药")
    compatibility_analysis: str = Field(..., description="配伍分析")
    synergy_effects: List[str] = Field(default_factory=list, description="协同作用")
    potential_conflicts: List[str] = Field(default_factory=list, description="潜在冲突")
    degraded: bool = Field(default=False, description="是否使用确定性规则降级结果")


class OptimizationSuggestion(BaseModel):
    """优化建议模型"""
    type: str = Field(..., description="优化类型: simplify/substitute/dosage/add/remove")
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议描述")
    reason: str = Field(..., description="建议理由")
    confidence: float = Field(..., ge=0, le=1, description="置信度")


class OptimizationChange(BaseModel):
    """优化方案中的一条结构化变更。"""
    action: str = Field(..., description="变更类型: adjust_dosage/remove_herb/substitute_herb/add_herb")
    herb_name: str = Field(..., description="目标药味")
    before: Optional[str] = Field(None, description="变更前")
    after: Optional[str] = Field(None, description="变更后")
    reason: str = Field(..., description="变更理由")


class OptimizationResult(BaseModel):
    """优化结果模型"""
    original_prescription: PrescriptionResponse
    optimized_prescription: PrescriptionResponse
    suggestions: List[OptimizationSuggestion]
    changes: List[OptimizationChange] = Field(default_factory=list, description="已形成的结构化变更")
    expected_improvements: List[str] = Field(default_factory=list, description="预期改进")
    risk_assessment: str = Field(..., description="风险评估")
    degraded: bool = Field(default=False, description="是否使用确定性规则降级结果")


class EfficacyPrediction(BaseModel):
    """药效预测模型"""
    prescription_id: int
    target_symptoms: List[str] = Field(..., description="目标症状")
    predicted_efficacy: float = Field(..., ge=0, le=100, description="预测疗效")
    confidence_level: float = Field(..., ge=0, le=1, description="置信度")
    mechanism_analysis: str = Field(..., description="作用机制分析")
    supporting_evidence: List[str] = Field(default_factory=list, description="支持证据")
    contraindications: List[str] = Field(default_factory=list, description="禁忌症")


class EfficacyPredictionRequest(BaseModel):
    """M04 药效预测请求。"""
    prescription_id: int = Field(..., gt=0, description="方剂 ID")
    target_symptoms: List[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="目标症状列表",
    )

    @validator("target_symptoms")
    def validate_target_symptoms(cls, value):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        if not cleaned:
            raise ValueError("至少需要提供一个目标症状")
        if any(len(item) > 50 for item in cleaned):
            raise ValueError("单个目标症状不能超过50个字符")
        return cleaned


class EfficacyPredictionResponse(EfficacyPrediction):
    """M04 药效预测响应。"""
    prediction_id: int
    risk_level: str = Field(..., pattern="^(low|medium|high)$", description="风险等级")
    degraded: bool = Field(default=False, description="是否使用本地规则降级")
    created_at: datetime


class AdminRoleUpdateRequest(BaseModel):
    """M06 修改用户角色请求。"""
    role: Literal["user", "admin"] = Field(..., description="用户角色")


class AdminStatusUpdateRequest(BaseModel):
    """M06 修改用户启停状态请求。"""
    is_active: bool = Field(..., description="是否启用")


class AncientBookResponse(BaseModel):
    """M05 古籍文献响应。"""
    id: int
    title: str
    dynasty: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    prescriptions: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    sort_order: int = 0

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """聊天消息。"""
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    """聊天请求。"""
    message: str = Field(..., min_length=1, max_length=10000)
    sessionId: str = Field(..., min_length=1, max_length=100)
    history: List[ChatMessage] = Field(default_factory=list, max_length=50)


class ChatResponse(BaseModel):
    """聊天响应数据。"""
    response: str
    sessionId: str
    timestamp: str
    persisted: bool = True


class RecommendationConstraints(BaseModel):
    """智能方剂推荐约束。"""
    avoid_herbs: List[str] = Field(default_factory=list, max_items=30)
    max_herb_count: Optional[int] = Field(None, ge=2, le=30)


class RecommendationRequest(BaseModel):
    """智能方剂推荐请求。"""
    symptoms: str = Field(..., min_length=2, max_length=1000)
    constraints: RecommendationConstraints = Field(
        default_factory=RecommendationConstraints
    )
    use_llm: bool = Field(default=True)


class RecommendationCandidate(BaseModel):
    """标准化推荐候选。"""
    prescription_id: Optional[int] = None
    name: str
    match_score: float = Field(..., ge=0, le=100)
    reasons: List[str] = Field(default_factory=list)
    core_herbs: List[str] = Field(default_factory=list)
    constraints_checked: bool = True
    source: str
    degraded: bool = False
    functions: Optional[str] = None
    indications: Optional[str] = None
    source_text: Optional[str] = None
    conflict_warnings: List[str] = Field(default_factory=list)


class RecommendationResult(BaseModel):
    """智能方剂推荐结果。"""
    recommendations: List[RecommendationCandidate] = Field(default_factory=list)
    syndrome: Optional[str] = None
    analysis: Optional[str] = None
    reason: Optional[str] = None
    degraded: bool = False


class ComparisonResult(BaseModel):
    """方剂对比结果"""
    prescriptions: List[PrescriptionResponse]
    comparison_dimensions: List[str] = Field(..., description="对比维度")
    scores: Dict[int, float] = Field(..., description="各方剂评分")
    dimension_scores: Dict[int, Dict[str, float]] = Field(
        default_factory=dict,
        description="各方剂在每个对比维度上的评分",
    )
    pros_cons: Dict[int, Dict[str, List[str]]] = Field(..., description="优缺点分析")
    recommendation: str = Field(..., description="推荐建议")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=500, description="每页数量")


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class APIResponse(BaseModel):
    """统一API响应模型"""
    code: str = Field(default="SUCCESS", description="响应代码")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
