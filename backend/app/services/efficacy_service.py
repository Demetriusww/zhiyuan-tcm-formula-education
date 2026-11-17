"""M04 药效预测服务。

优先使用大模型生成结果；模型不可用时，根据方剂功效、主治、目标症状和
十八反、十九畏规则生成确定性的本地结果。
"""
import json
from datetime import datetime
from typing import List, Tuple

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import DatabaseError, NotFoundError
from app.core.logger import analysis_logger
from app.models.database_models import (
    EfficacyPrediction as EfficacyPredictionModel,
    Prescription,
    PrescriptionHerb as PrescriptionHerbModel,
)
from app.models.schemas import (
    EfficacyPrediction,
    EfficacyPredictionResponse,
    PrescriptionHerb,
)
from app.services.algorithm.compatibility_checker import checker
from app.services.llm_service import llm_service


class EfficacyService:
    """药效预测业务服务。"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = llm_service

    async def predict(
        self,
        prescription_id: int,
        target_symptoms: List[str],
        user_id: int,
    ) -> EfficacyPredictionResponse:
        """预测方剂对目标症状的疗效并保存记录。"""
        prescription = self._get_prescription(prescription_id)
        herbs = [
            PrescriptionHerb(
                herb_id=item.herb_id,
                name=item.herb.name if item.herb else "",
                dosage=item.dosage or "",
                preparation=item.preparation,
                order=item.order or 0,
            )
            for item in prescription.herbs
            if item.herb
        ]
        symptoms = self._normalize_symptoms(target_symptoms)

        degraded = False
        try:
            result = await self.llm_service.predict_efficacy(
                prescription_name=prescription.name,
                herbs=herbs,
                target_symptoms=symptoms,
            )
            result.prescription_id = prescription.id
            result.target_symptoms = symptoms
        except Exception as exc:
            degraded = True
            analysis_logger.warning(
                "大模型药效预测不可用，使用规则引擎降级: %s (%s)",
                prescription.name,
                exc,
            )
            result = self._fallback_prediction(prescription, herbs, symptoms)

        contraindications = self._normalize_list(result.contraindications)
        risk_level = self._risk_level(
            herbs=[item.name for item in herbs],
            predicted_efficacy=result.predicted_efficacy,
            confidence_level=result.confidence_level,
            contraindications=contraindications,
        )

        try:
            record = EfficacyPredictionModel(
                user_id=user_id,
                prescription_id=prescription.id,
                target_symptoms=self._json_list(symptoms),
                predicted_efficacy=result.predicted_efficacy,
                confidence_level=result.confidence_level,
                mechanism_analysis=result.mechanism_analysis,
                supporting_evidence=self._json_list(result.supporting_evidence),
                contraindications=self._json_list(contraindications),
                risk_level=risk_level,
                created_at=datetime.utcnow(),
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
        except Exception as exc:
            self.db.rollback()
            raise DatabaseError(f"保存药效预测记录失败: {exc}") from exc

        return EfficacyPredictionResponse(
            prediction_id=record.id,
            prescription_id=prescription.id,
            target_symptoms=symptoms,
            predicted_efficacy=result.predicted_efficacy,
            confidence_level=result.confidence_level,
            mechanism_analysis=result.mechanism_analysis,
            supporting_evidence=self._normalize_list(result.supporting_evidence),
            contraindications=contraindications,
            risk_level=risk_level,
            degraded=degraded,
            created_at=record.created_at,
        )

    def _get_prescription(self, prescription_id: int) -> Prescription:
        prescription = (
            self.db.query(Prescription)
            .options(
                joinedload(Prescription.herbs).joinedload(
                    PrescriptionHerbModel.herb
                )
            )
            .filter(Prescription.id == prescription_id)
            .first()
        )
        if not prescription:
            raise NotFoundError(f"方剂ID {prescription_id} 不存在")
        return prescription

    def _fallback_prediction(
        self,
        prescription: Prescription,
        herbs: List[PrescriptionHerb],
        symptoms: List[str],
    ) -> EfficacyPrediction:
        functions = (prescription.functions or "").strip()
        indications = (prescription.indications or "").strip()
        source_text = " ".join([prescription.name, functions, indications])
        matched_symptoms = [
            symptom
            for symptom in symptoms
            if symptom and symptom in source_text
        ]

        efficacy = 50.0
        if functions:
            efficacy += 8.0
        if indications:
            efficacy += 6.0
        if 4 <= len(herbs) <= 12:
            efficacy += 7.0
        efficacy += min(21.0, len(matched_symptoms) * 7.0)

        conflicts = checker.check([item.name for item in herbs])
        high_conflicts = [item for item in conflicts if item["level"] == "high"]
        warning_conflicts = [item for item in conflicts if item["level"] != "high"]
        efficacy -= len(high_conflicts) * 16.0
        efficacy -= len(warning_conflicts) * 8.0
        efficacy = round(max(0.0, min(100.0, efficacy)), 1)

        confidence = 0.55 + min(0.18, len(matched_symptoms) * 0.06)
        if functions and indications:
            confidence += 0.08
        if conflicts:
            confidence -= 0.08
        confidence = round(max(0.35, min(0.9, confidence)), 2)

        evidence: List[str] = []
        if matched_symptoms:
            evidence.append(
                "目标症状与方剂功效或主治描述匹配："
                + "、".join(matched_symptoms)
            )
        if functions:
            evidence.append(f"方剂功效：{functions}")
        if indications:
            evidence.append(f"方剂主治：{indications}")
        if prescription.source:
            evidence.append(f"方剂来源：{prescription.source}")
        evidence.append(f"方剂共收录{len(herbs)}味药材")

        contraindications: List[str] = []
        if prescription.precautions:
            contraindications.append(prescription.precautions.strip())
        for conflict in conflicts:
            contraindications.append(
                f"{conflict['herb_a']}与{conflict['herb_b']}命中"
                f"{conflict['rule_type']}：{conflict['description']}"
            )

        if matched_symptoms:
            mechanism = (
                f"方剂功效为“{functions or '未收录'}”，主治为"
                f"“{indications or '未收录'}”。目标症状"
                f"“{'、'.join(matched_symptoms)}”可与上述功效和主治方向对应，"
                "但本结果仅基于文本匹配和配伍规则，不能替代临床辨证。"
            )
        else:
            mechanism = (
                f"未在方剂功效和主治中发现与"
                f"“{'、'.join(symptoms)}”的直接文本匹配。"
                "当前评分主要依据药味数量、方剂基础信息和配伍禁忌生成，"
                "需由执业中医师结合证候进一步判断。"
            )

        return EfficacyPrediction(
            prescription_id=prescription.id,
            target_symptoms=symptoms,
            predicted_efficacy=efficacy,
            confidence_level=confidence,
            mechanism_analysis=mechanism,
            supporting_evidence=evidence,
            contraindications=contraindications,
        )

    @staticmethod
    def _risk_level(
        herbs: List[str],
        predicted_efficacy: float,
        confidence_level: float,
        contraindications: List[str],
    ) -> str:
        summary = checker.check_with_summary(herbs)
        conflicts = summary["conflicts"]
        if any(item["level"] == "high" for item in conflicts):
            return "high"
        if conflicts:
            return "medium"
        if (
            len(contraindications) >= 2
            or predicted_efficacy < 55
            or confidence_level < 0.55
        ):
            return "medium"
        return "low"

    @staticmethod
    def _normalize_symptoms(symptoms: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()
        for item in symptoms:
            text = str(item).strip()
            if text and text not in seen:
                seen.add(text)
                cleaned.append(text)
        if not cleaned:
            raise ValueError("至少需要提供一个目标症状")
        return cleaned

    @staticmethod
    def _normalize_list(values: List[str]) -> List[str]:
        return [str(item).strip() for item in values if str(item).strip()]

    @staticmethod
    def _json_list(values: List[str]) -> str:
        return json.dumps(
            [str(item).strip() for item in values if str(item).strip()],
            ensure_ascii=False,
        )
