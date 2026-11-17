"""方剂服务。

M01 负责方剂 CRUD、服务端筛选/排序/分页；M03 提供确定性的分析、
优化和对比能力，并在大模型不可用时自动降级。
"""
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import (
    DatabaseError,
    DuplicateError,
    LLMServiceError,
    NotFoundError,
    ValidationError,
)
from app.core.logger import analysis_logger, db_logger
from app.models.database_models import (
    AnalysisRecord,
    EfficacyPrediction,
    Favorite,
    Herb,
    Prescription,
    PrescriptionHerb as PrescriptionHerbModel,
)
from app.models.schemas import (
    CompatibilityAnalysis,
    ComparisonResult,
    OptimizationChange,
    OptimizationResult,
    OptimizationSuggestion,
    PaginatedResponse,
    PaginationParams,
    PrescriptionCreate,
    PrescriptionHerb,
    PrescriptionResponse,
    PrescriptionUpdate,
)
from app.services.algorithm.compatibility_checker import checker
from app.services.llm_service import llm_service


SORT_FIELDS = {"name", "created_at", "updated_at"}
SORT_ORDERS = {"asc", "desc"}


class PrescriptionService:
    """方剂业务服务。"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = llm_service

    # ==================== M01 CRUD ====================

    async def create_prescription(
        self,
        prescription_data: PrescriptionCreate,
    ) -> PrescriptionResponse:
        """创建新方剂。"""
        name = self._normalize_name(prescription_data.name)
        try:
            if self._name_exists(name):
                raise DuplicateError(f"方剂 '{name}' 已存在")

            await self._validate_herbs(prescription_data.herbs)

            now = datetime.now()
            prescription = Prescription(
                name=name,
                pinyin=prescription_data.pinyin,
                type=self._type_value(prescription_data.type),
                source=prescription_data.source,
                functions=prescription_data.functions,
                indications=prescription_data.indications,
                usage=prescription_data.usage,
                precautions=prescription_data.precautions,
                category=prescription_data.category,
                created_at=now,
                updated_at=now,
            )
            self.db.add(prescription)
            self.db.flush()

            self._replace_herbs(prescription.id, prescription_data.herbs)
            self.db.commit()
            db_logger.info("创建方剂成功: %s (ID: %s)", name, prescription.id)
            return await self.get_prescription(prescription.id)

        except (DuplicateError, ValidationError):
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateError(f"方剂 '{name}' 已存在") from exc
        except Exception as exc:
            self.db.rollback()
            db_logger.error("创建方剂失败: %s", exc)
            raise DatabaseError(f"创建方剂失败: {exc}") from exc

    async def get_prescription(self, prescription_id: int) -> PrescriptionResponse:
        """获取方剂详情。"""
        prescription = self._base_query().filter(Prescription.id == prescription_id).first()
        if not prescription:
            raise NotFoundError(f"方剂ID {prescription_id} 不存在")
        return self._to_response(prescription)

    async def update_prescription(
        self,
        prescription_id: int,
        update_data: PrescriptionUpdate,
    ) -> PrescriptionResponse:
        """更新方剂，传入 herbs 时整体替换组成。"""
        try:
            prescription = self.db.query(Prescription).filter(
                Prescription.id == prescription_id
            ).first()
            if not prescription:
                raise NotFoundError(f"方剂ID {prescription_id} 不存在")

            values = update_data.dict(exclude_unset=True)
            herbs = values.pop("herbs", None)

            if "name" in values:
                values["name"] = self._normalize_name(values["name"])
                if self._name_exists(values["name"], exclude_id=prescription_id):
                    raise DuplicateError(f"方剂名称 '{values['name']}' 已存在")
            if "type" in values:
                values["type"] = self._type_value(values["type"])

            for key, value in values.items():
                setattr(prescription, key, value)
            prescription.updated_at = datetime.now()

            if herbs is not None:
                await self._validate_herbs(herbs)
                self._replace_herbs(prescription_id, herbs)

            self.db.commit()
            db_logger.info("更新方剂成功: %s (ID: %s)", prescription.name, prescription_id)
            return await self.get_prescription(prescription_id)

        except (NotFoundError, DuplicateError, ValidationError):
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateError(f"方剂名称 '{update_data.name}' 已存在") from exc
        except Exception as exc:
            self.db.rollback()
            db_logger.error("更新方剂失败: %s", exc)
            raise DatabaseError(f"更新方剂失败: {exc}") from exc

    async def delete_prescription(self, prescription_id: int) -> bool:
        """删除方剂、药味关联和收藏关联。"""
        try:
            prescription = self.db.query(Prescription).filter(
                Prescription.id == prescription_id
            ).first()
            if not prescription:
                raise NotFoundError(f"方剂ID {prescription_id} 不存在")

            # SQLite 默认不一定启用外键级联，因此在应用层显式清理引用。
            self.db.query(PrescriptionHerbModel).filter(
                PrescriptionHerbModel.prescription_id == prescription_id
            ).delete(synchronize_session=False)
            self.db.query(Favorite).filter(
                Favorite.prescription_id == prescription_id
            ).delete(synchronize_session=False)
            self.db.query(AnalysisRecord).filter(
                AnalysisRecord.prescription_id == prescription_id
            ).delete(synchronize_session=False)
            self.db.query(EfficacyPrediction).filter(
                EfficacyPrediction.prescription_id == prescription_id
            ).delete(synchronize_session=False)
            self.db.delete(prescription)
            self.db.commit()

            db_logger.info("删除方剂成功: ID %s", prescription_id)
            return True
        except NotFoundError:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            db_logger.error("删除方剂失败: %s", exc)
            raise DatabaseError(f"删除方剂失败: {exc}") from exc

    async def list_prescriptions(
        self,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> PaginatedResponse:
        """分页获取方剂列表，筛选和排序全部在数据库执行。"""
        try:
            query = self._filtered_query(filters or {}, sort_by, sort_order)
            total = query.count()
            offset = (pagination.page - 1) * pagination.page_size
            rows = query.offset(offset).limit(pagination.page_size).all()
            items = [self._to_response(row) for row in rows]
            total_pages = (total + pagination.page_size - 1) // pagination.page_size
            return PaginatedResponse(
                items=items,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=total_pages,
            )
        except ValidationError:
            raise
        except Exception as exc:
            db_logger.error("获取方剂列表失败: %s", exc)
            raise DatabaseError(f"获取方剂列表失败: {exc}") from exc

    async def search_prescriptions(
        self,
        query: str,
        pagination: PaginationParams,
    ) -> PaginatedResponse:
        """兼容搜索入口，语义等同于列表 keyword 筛选。"""
        return await self.list_prescriptions(pagination, {"keyword": query})

    async def get_all_prescriptions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[PrescriptionResponse]:
        """获取全部匹配方剂，供导出使用（忽略分页）。"""
        query = self._filtered_query(filters or {}, sort_by, sort_order)
        return [self._to_response(row) for row in query.all()]

    # ==================== M03 analysis / optimization ====================

    async def analyze_compatibility(self, prescription_id: int) -> CompatibilityAnalysis:
        """分析方剂配伍。"""
        prescription = await self.get_prescription(prescription_id)
        analysis_logger.info("开始配伍分析: %s", prescription.name)
        try:
            result = await self.llm_service.analyze_compatibility(
                prescription_name=prescription.name,
                herbs=prescription.herbs,
            )
            result.degraded = False
            analysis_logger.info(
                "配伍分析完成: %s, 评分: %s",
                prescription.name,
                result.overall_score,
            )
            return result
        except Exception as exc:
            analysis_logger.warning(
                "大模型配伍分析不可用，使用规则引擎降级: %s (%s)",
                prescription.name,
                exc,
            )
            return self._build_compatibility_analysis(prescription)

    async def optimize_prescription(
        self,
        prescription_id: int,
        target_symptoms: Optional[List[str]] = None,
    ) -> OptimizationResult:
        """生成结构化优化方案，模型不可用时仍返回确定性建议。"""
        original = await self.get_prescription(prescription_id)
        analysis_logger.info("开始方剂优化: %s", original.name)
        degraded = False
        try:
            suggestions = await self.llm_service.generate_optimization_suggestions(
                prescription_name=original.name,
                herbs=original.herbs,
                target_symptoms=target_symptoms,
            )
        except Exception as exc:
            degraded = True
            analysis_logger.warning(
                "大模型优化建议不可用，使用规则引擎降级: %s (%s)",
                original.name,
                exc,
            )
            suggestions = []

        if not suggestions:
            degraded = True
            suggestions = self._fallback_optimization_suggestions(
                original,
                target_symptoms or [],
            )

        optimized, changes = self._build_optimized_prescription(original)
        expected_improvements = [item.title for item in suggestions]
        if changes and not expected_improvements:
            expected_improvements = [item.reason for item in changes]

        conflict_count = len(checker.check([item.name for item in original.herbs]))
        if conflict_count:
            risk_assessment = (
                f"检测到{conflict_count}条十八反或十九畏冲突。优化方案仅作为"
                "复核建议，临床应用前必须由执业中医师确认。"
            )
        elif degraded:
            risk_assessment = (
                "当前结果由确定性规则生成，未完成大模型复核。剂量和替换"
                "建议需结合患者体质与执业医师意见确认。"
            )
        else:
            risk_assessment = (
                "方案基于方剂组成和公开配伍规则生成，仍需结合患者体质、"
                "证候变化和执业医师意见使用。"
            )

        return OptimizationResult(
            original_prescription=original,
            optimized_prescription=optimized,
            suggestions=suggestions,
            changes=changes,
            expected_improvements=expected_improvements,
            risk_assessment=risk_assessment,
            degraded=degraded,
        )

    async def compare_prescriptions(self, prescription_ids: List[int]) -> ComparisonResult:
        """按药效、安全性、药味数量和剂量合理性对比方剂。"""
        if len(prescription_ids) < 2:
            raise ValidationError("至少需要2个方剂进行对比")
        if len(prescription_ids) > 5:
            raise ValidationError("最多支持5个方剂进行对比")
        if len(prescription_ids) != len(set(prescription_ids)):
            raise ValidationError("对比列表不能包含重复方剂")

        prescriptions = [await self.get_prescription(pid) for pid in prescription_ids]
        scores: Dict[int, float] = {}
        dimension_scores: Dict[int, Dict[str, float]] = {}
        pros_cons: Dict[int, Dict[str, List[str]]] = {}
        for prescription in prescriptions:
            dimensions = self._score_prescription(prescription)
            dimension_scores[prescription.id] = dimensions
            scores[prescription.id] = round(
                dimensions["功效"]
                * 0.3
                + dimensions["安全性"] * 0.25
                + dimensions["药味数量"] * 0.15
                + dimensions["剂量合理性"] * 0.15
                + dimensions["配伍协调"] * 0.15,
                1,
            )
            pros_cons[prescription.id] = self._build_pros_cons(
                prescription,
                dimensions,
            )

        best_id = max(scores, key=lambda item: (scores[item], item))
        best_name = next(p.name for p in prescriptions if p.id == best_id)
        best_dimension = max(
            dimension_scores[best_id],
            key=dimension_scores[best_id].get,
        )
        return ComparisonResult(
            prescriptions=prescriptions,
            comparison_dimensions=["功效", "安全性", "药味数量", "剂量合理性", "配伍协调"],
            scores=scores,
            dimension_scores=dimension_scores,
            pros_cons=pros_cons,
            recommendation=(
                f"综合评分最高的是 {best_name}（{scores[best_id]} 分），"
                f"其中“{best_dimension}”维度表现最突出。该结果仅用于辅助比较，"
                "最终选方需结合辨证结果。"
            ),
        )

    def _build_compatibility_analysis(
        self,
        prescription: PrescriptionResponse,
    ) -> CompatibilityAnalysis:
        herb_names = [item.name for item in prescription.herbs]
        summary = checker.check_with_summary(herb_names)
        conflicts = summary["conflicts"]
        high_conflicts = sum(1 for item in conflicts if item["level"] == "high")
        warning_conflicts = len(conflicts) - high_conflicts
        score = 88.0 - high_conflicts * 20.0 - warning_conflicts * 12.0
        if prescription.functions:
            score += 3.0
        if prescription.indications:
            score += 3.0
        if not conflicts and len(herb_names) >= 4:
            score += 4.0
        score = self._clamp(score)

        monarch, ministers, assistants, messengers = self._assign_roles(
            prescription.herbs
        )
        conflict_messages = [
            (
                f"{item['herb_a']}与{item['herb_b']}命中{item['rule_type']}"
                f"（{item['rule_name']}）：{item['description']}"
            )
            for item in conflicts
        ]
        synergy_effects: List[str] = []
        if prescription.functions:
            synergy_effects.append(f"全方功效方向：{prescription.functions}")
        herb_count = len(prescription.herbs)
        if 4 <= herb_count <= 12:
            synergy_effects.append("药味数量处于常见方剂区间，便于发挥协同作用")
        if conflicts:
            synergy_effects.append("存在需优先处理的配伍禁忌，安全性评分已相应下调")
        else:
            synergy_effects.append("未命中十八反、十九畏规则，配伍禁忌风险较低")

        role_text = (
            f"君药为{monarch.name}；"
            f"臣药为{'、'.join(item.name for item in ministers) or '未明确'}；"
            f"佐药为{'、'.join(item.name for item in assistants) or '未明确'}；"
            f"使药为{'、'.join(item.name for item in messengers) or '未明确'}。"
        )
        conflict_text = (
            f"检出{len(conflicts)}条潜在冲突。" if conflicts else "未检出已知配伍禁忌。"
        )
        if conflicts:
            conflict_text += "建议逐条核对剂量、炮制方式和患者禁忌后再使用。"
        else:
            conflict_text += "该结论仅覆盖规则库中的十八反、十九畏条目。"

        return CompatibilityAnalysis(
            prescription_name=prescription.name,
            overall_score=score,
            monarch_herb=monarch,
            minister_herbs=ministers,
            assistant_herbs=assistants,
            messenger_herbs=messengers,
            compatibility_analysis=f"{role_text}{conflict_text}",
            synergy_effects=synergy_effects,
            potential_conflicts=conflict_messages,
            degraded=True,
        )

    def _fallback_optimization_suggestions(
        self,
        prescription: PrescriptionResponse,
        target_symptoms: List[str],
    ) -> List[OptimizationSuggestion]:
        herb_names = [item.name for item in prescription.herbs]
        conflicts = checker.check(herb_names)
        suggestions: List[OptimizationSuggestion] = []
        if conflicts:
            conflict = conflicts[0]
            suggestions.append(
                OptimizationSuggestion(
                    type="remove",
                    title=f"复核并考虑移除{conflict['herb_b']}",
                    description=(
                        f"{conflict['herb_a']}与{conflict['herb_b']}命中"
                        f"{conflict['rule_type']}，应优先由医师复核该药味。"
                    ),
                    reason="降低已知配伍禁忌风险",
                    confidence=0.9,
                )
            )

        if len(prescription.herbs) > 10:
            suggestions.append(
                OptimizationSuggestion(
                    type="simplify",
                    title="复核药味数量",
                    description=(
                        f"当前共{len(prescription.herbs)}味药，可结合主次证候"
                        "评估是否存在可精简药味。"
                    ),
                    reason="减少不必要的药味和潜在相互作用",
                    confidence=0.7,
                )
            )

        target_text = "、".join(target_symptoms) if target_symptoms else "当前辨证目标"
        suggestions.append(
            OptimizationSuggestion(
                type="dosage",
                title="复核君药剂量",
                description=(
                    f"围绕“{target_text}”重新评估{prescription.herbs[0].name}"
                    "的剂量，并在安全范围内形成调整方案。"
                ),
                reason="让主要药味剂量与目标证候和患者体质相协调",
                confidence=0.68,
            )
        )
        return suggestions

    def _build_optimized_prescription(
        self,
        original: PrescriptionResponse,
    ) -> tuple[PrescriptionResponse, List[OptimizationChange]]:
        optimized = original.copy(deep=True)
        optimized.herbs = [item.copy(deep=True) for item in original.herbs]
        changes: List[OptimizationChange] = []
        conflicts = checker.check([item.name for item in original.herbs])

        if conflicts and len(optimized.herbs) > 2:
            blocked_names = {
                conflicts[0]["herb_a"],
                conflicts[0]["herb_b"],
            }
            remove_index = next(
                (
                    index
                    for index, item in enumerate(optimized.herbs)
                    if item.name in blocked_names
                ),
                len(optimized.herbs) - 1,
            )
            removed = optimized.herbs.pop(remove_index)
            changes.append(
                OptimizationChange(
                    action="remove_herb",
                    herb_name=removed.name,
                    before=f"{removed.name} {removed.dosage}".strip(),
                    after=None,
                    reason=(
                        f"{conflicts[0]['herb_a']}与{conflicts[0]['herb_b']}"
                        f"命中{conflicts[0]['rule_type']}，优先移除风险药味供复核"
                    ),
                )
            )
        elif len(optimized.herbs) > 10:
            removed = optimized.herbs.pop()
            changes.append(
                OptimizationChange(
                    action="remove_herb",
                    herb_name=removed.name,
                    before=f"{removed.name} {removed.dosage}".strip(),
                    after=None,
                    reason="原方药味较多，移除末位辅助药味以形成精简复核方案",
                )
            )

        adjusted = optimized.herbs[0]
        before_dosage = adjusted.dosage or "未标明"
        after_dosage = self._increase_dosage(before_dosage)
        adjusted.dosage = after_dosage
        changes.append(
            OptimizationChange(
                action="adjust_dosage",
                herb_name=adjusted.name,
                before=before_dosage,
                after=after_dosage,
                reason="对君药剂量进行保守上调，供结合证候和体质进一步复核",
            )
        )
        for index, item in enumerate(optimized.herbs, start=1):
            item.order = index
        return optimized, changes

    def _score_prescription(
        self,
        prescription: PrescriptionResponse,
    ) -> Dict[str, float]:
        herb_count = len(prescription.herbs)
        conflict_summary = checker.check_with_summary(
            [item.name for item in prescription.herbs]
        )
        conflicts = conflict_summary["conflicts"]
        high_count = sum(1 for item in conflicts if item["level"] == "high")
        warning_count = len(conflicts) - high_count

        efficacy = 68.0
        if prescription.functions:
            efficacy += 12.0
        if prescription.indications:
            efficacy += 12.0
        if 4 <= herb_count <= 12:
            efficacy += 8.0
        elif herb_count > 12:
            efficacy += 3.0

        safety = 100.0 - high_count * 22.0 - warning_count * 14.0
        if prescription.precautions:
            safety -= 3.0

        if 4 <= herb_count <= 12:
            herb_count_score = 100.0 - abs(8 - herb_count) * 4.0
        elif herb_count < 4:
            herb_count_score = 70.0 - (4 - herb_count) * 10.0
        else:
            herb_count_score = 78.0 - (herb_count - 12) * 5.0

        numeric_dosages = [
            self._parse_dosage(item.dosage)
            for item in prescription.herbs
        ]
        valid_dosages = [value for value in numeric_dosages if value is not None]
        if not valid_dosages:
            dosage_score = 55.0
        else:
            coverage = len(valid_dosages) / max(1, herb_count)
            plausible = sum(1 for value in valid_dosages if 1 <= value <= 60)
            plausibility = plausible / len(valid_dosages)
            dosage_score = 55.0 + coverage * 20.0 + plausibility * 25.0

        compatibility = 100.0 - high_count * 20.0 - warning_count * 12.0
        return {
            "功效": round(self._clamp(efficacy), 1),
            "安全性": round(self._clamp(safety), 1),
            "药味数量": round(self._clamp(herb_count_score), 1),
            "剂量合理性": round(self._clamp(dosage_score), 1),
            "配伍协调": round(self._clamp(compatibility), 1),
        }

    def _build_pros_cons(
        self,
        prescription: PrescriptionResponse,
        dimensions: Dict[str, float],
    ) -> Dict[str, List[str]]:
        pros: List[str] = []
        cons: List[str] = []
        herb_count = len(prescription.herbs)
        if prescription.functions:
            pros.append(f"功效明确：{prescription.functions}")
        if prescription.indications:
            pros.append(f"主治明确：{prescription.indications}")
        if dimensions["安全性"] >= 90:
            pros.append("未检出十八反、十九畏高风险冲突")
        if 4 <= herb_count <= 12:
            pros.append(f"{herb_count}味药的组方规模较均衡")

        if dimensions["安全性"] < 90:
            cons.append("存在配伍禁忌或安全性风险，需逐条复核")
        if herb_count > 12:
            cons.append(f"共{herb_count}味药，药味较多且相互作用复杂")
        if herb_count < 4:
            cons.append(f"仅{herb_count}味药，需确认能否覆盖目标证候")
        if dimensions["剂量合理性"] < 75:
            cons.append("部分药味缺少可解析剂量或剂量范围需复核")
        if not prescription.precautions:
            cons.append("未填写禁忌与注意事项")
        return {"pros": pros or ["基础字段完整"], "cons": cons or ["未发现明显结构性问题"]}

    @staticmethod
    def _assign_roles(
        herbs: List[PrescriptionHerb],
    ) -> tuple[
        PrescriptionHerb,
        List[PrescriptionHerb],
        List[PrescriptionHerb],
        List[PrescriptionHerb],
    ]:
        if not herbs:
            raise ValidationError("方剂至少需要2味药物")
        if len(herbs) == 2:
            return herbs[0], [herbs[1]], [], []
        if len(herbs) == 3:
            return herbs[0], [herbs[1]], [herbs[2]], []
        return herbs[0], [herbs[1]], herbs[2:-1], [herbs[-1]]

    @staticmethod
    def _parse_dosage(dosage: Optional[str]) -> Optional[float]:
        if not dosage:
            return None
        match = re.search(r"(\d+(?:\.\d+)?)", dosage)
        return float(match.group(1)) if match else None

    @classmethod
    def _increase_dosage(cls, dosage: str) -> str:
        value = cls._parse_dosage(dosage)
        if value is None:
            return f"{dosage}（建议复核）" if dosage else "建议复核剂量"
        increment = max(1.0, round(value * 0.1, 1))
        adjusted = round(value + increment, 1)
        unit = re.sub(r"^\s*\d+(?:\.\d+)?\s*", "", dosage).strip() or "g"
        if adjusted.is_integer():
            adjusted_text = str(int(adjusted))
        else:
            adjusted_text = str(adjusted)
        return f"{adjusted_text}{unit}"

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        return max(minimum, min(maximum, value))

    # ==================== query helpers ====================

    def _base_query(self):
        return self.db.query(Prescription).options(
            joinedload(Prescription.herbs).joinedload(PrescriptionHerbModel.herb)
        )

    def _filtered_query(
        self,
        filters: Dict[str, Any],
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ):
        query = self._base_query()
        keyword = self._clean_text(filters.get("keyword"))
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    Prescription.name.ilike(pattern),
                    Prescription.functions.ilike(pattern),
                    Prescription.indications.ilike(pattern),
                )
            )

        name = self._clean_text(filters.get("name"))
        if name:
            query = query.filter(Prescription.name.ilike(f"%{name}%"))
        type_value = self._clean_text(filters.get("type"))
        if type_value:
            query = query.filter(Prescription.type == type_value)
        category = self._clean_text(filters.get("category"))
        if category:
            query = query.filter(Prescription.category == category)

        sort_field = sort_by or "updated_at"
        direction = (sort_order or "desc").lower()
        if sort_field not in SORT_FIELDS:
            raise ValidationError("排序字段必须是 name、created_at 或 updated_at")
        if direction not in SORT_ORDERS:
            raise ValidationError("排序方向必须是 asc 或 desc")
        column = getattr(Prescription, sort_field)
        query = query.order_by(asc(column) if direction == "asc" else desc(column))
        return query

    def _replace_herbs(self, prescription_id: int, herbs: Iterable[PrescriptionHerb]) -> None:
        self.db.query(PrescriptionHerbModel).filter(
            PrescriptionHerbModel.prescription_id == prescription_id
        ).delete(synchronize_session=False)
        for index, item in enumerate(herbs, start=1):
            self.db.add(
                PrescriptionHerbModel(
                    prescription_id=prescription_id,
                    herb_id=item.herb_id,
                    dosage=(item.dosage or "").strip() or None,
                    preparation=(item.preparation or "").strip() or None,
                    order=item.order or index,
                )
            )

    def _to_response(self, prescription: Prescription) -> PrescriptionResponse:
        herbs: List[PrescriptionHerb] = []
        for item in prescription.herbs or []:
            herb_name = item.herb.name if item.herb else ""
            herbs.append(
                PrescriptionHerb(
                    herb_id=item.herb_id,
                    name=herb_name,
                    dosage=item.dosage or "",
                    preparation=item.preparation,
                    order=item.order or 0,
                )
            )
        return PrescriptionResponse(
            id=prescription.id,
            name=prescription.name,
            pinyin=prescription.pinyin,
            type=prescription.type or "经典名方",
            source=prescription.source,
            functions=prescription.functions,
            indications=prescription.indications,
            usage=prescription.usage,
            precautions=prescription.precautions,
            category=prescription.category,
            herbs=herbs,
            created_at=prescription.created_at,
            updated_at=prescription.updated_at,
        )

    def _name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Prescription).filter(func.trim(Prescription.name) == name)
        if exclude_id is not None:
            query = query.filter(Prescription.id != exclude_id)
        return query.first() is not None

    async def _validate_herbs(self, herbs: List[PrescriptionHerb]) -> None:
        if len(herbs) < 2:
            raise ValidationError("方剂至少需要2味药物")
        if len(herbs) > 30:
            raise ValidationError("方剂最多包含30味药物")

        ids = [item.herb_id for item in herbs]
        if len(ids) != len(set(ids)):
            raise ValidationError("同一方剂不能重复添加同一味药材")
        existing = {
            row.id: row
            for row in self.db.query(Herb).filter(Herb.id.in_(ids)).all()
        }
        missing = [str(herb_id) for herb_id in ids if herb_id not in existing]
        if missing:
            raise ValidationError(f"药材ID不存在: {', '.join(missing)}")

        # 对直接调用 API 的客户端校验名称和 ID 的一致性；导入服务会先解析再构造。
        for item in herbs:
            expected = existing[item.herb_id].name
            if item.name and item.name.strip() != expected:
                raise ValidationError(
                    f"药材ID {item.herb_id} 对应的名称应为“{expected}”"
                )

    async def _get_prescription_herbs(self, prescription_id: int) -> List[PrescriptionHerb]:
        """兼容旧调用：返回指定方剂的标准药味列表。"""
        rows = self.db.query(PrescriptionHerbModel).options(
            joinedload(PrescriptionHerbModel.herb)
        ).filter(
            PrescriptionHerbModel.prescription_id == prescription_id
        ).order_by(PrescriptionHerbModel.order).all()
        return [
            PrescriptionHerb(
                herb_id=row.herb_id,
                name=row.herb.name if row.herb else "",
                dosage=row.dosage or "",
                preparation=row.preparation,
                order=row.order or 0,
            )
            for row in rows
            if row.herb
        ]

    @staticmethod
    def _normalize_name(name: str) -> str:
        return (name or "").strip()

    @staticmethod
    def _clean_text(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _type_value(value: Any) -> str:
        return value.value if hasattr(value, "value") else str(value or "经典名方")
