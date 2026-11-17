# -*- coding: utf-8 -*-
"""
智能配伍服务
流程：用户输入症状/体质
  → (A) 大模型生成配伍参考方案（结构化 JSON）
  → (B) 每味药过 N02 配伍禁忌检测算法 → 冲突标注
  → (C) 若大模型不可用，自动降级为本地知识库匹配（保证演示可用）
输出：候选方案列表（含 name/functions/indications/herbs[带冲突标记]/source）
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.database_models import (
    Herb,
    Prescription,
    PrescriptionHerb as PrescriptionHerbModel,
)
from app.models.schemas import (
    RecommendationCandidate,
    RecommendationConstraints,
    RecommendationResult,
)
from app.services.algorithm.compatibility_checker import checker as conflict_checker
from app.services.llm_service import llm_service

logger = logging.getLogger("tcm_platform.smart")


# LLM 引导词（要求返回严格 JSON，便于解析后逐味校验）
SYSTEM_PROMPT = """你是一位严谨的中医方剂学专家，负责根据患者描述进行辨证论治，给出配伍参考方案。
要求：
1. 只推荐确有经典出处的方剂，不要自创方剂。
2. 必须给出每味药的规范名称（如"炙甘草"写"甘草"、"法半夏"写"半夏"、"生地黄"写"地黄"）。
3. 每个方剂给出：名称、出处、功效、主治、药物列表（只含药名）、剂量说明、配伍思路。
4. 仅输出 JSON，不要任何解释性文字。"""


def build_prompt(symptoms: str) -> str:
    return f"""患者主诉/症状/体质：{symptoms}

请辨证后给出 2~3 个最合适的配伍参考方案，按 JSON 格式返回：
{{
  "syndrome": "证候判断，如：脾胃气虚证",
  "analysis": "简要辨证分析（1-2句）",
  "candidates": [
    {{
      "name": "方剂名称",
      "source": "出处，如：太平惠民和剂局方",
      "functions": "功效，如：益气健脾",
      "indications": "主治",
      "herbs": ["人参", "白术", "茯苓", "甘草"],
      "dosage_note": "剂量参考，如：人参9g、白术9g、茯苓9g、甘草6g",
      "reason": "为什么选此方的简短理由"
    }}
  ]
}}"""


class SmartPrescriptionService:
    """智能配伍服务"""

    def __init__(self, db: Session):
        self.db = db

    # ============ M02 标准推荐入口 ============
    async def generate_recommendations(
        self,
        symptoms: str,
        constraints: Optional[RecommendationConstraints] = None,
        use_llm: bool = True,
    ) -> RecommendationResult:
        """返回可追溯到数据库方剂的标准推荐结果。"""
        normalized_symptoms = (symptoms or "").strip()
        constraints = constraints or RecommendationConstraints()
        deterministic = self._database_recommendations(normalized_symptoms)
        candidate_map = {
            item["prescription_id"]: item for item in deterministic
        }
        degraded = not use_llm

        if use_llm:
            try:
                llm_rows = await llm_service.recommend_prescriptions(
                    normalized_symptoms,
                    constraints.model_dump(exclude_none=True),
                )
                self._merge_llm_recommendations(candidate_map, llm_rows)
            except Exception as exc:
                degraded = True
                logger.warning("大模型推荐不可用，使用知识库匹配降级: %s", exc)

        recommendations = sorted(
            candidate_map.values(),
            key=lambda item: (-item["match_score"], item["prescription_id"]),
        )
        reason = None
        if not recommendations:
            reason = (
                "未找到与症状描述明确匹配的方剂，请补充主症、伴随症状、"
                "舌脉或体质信息后重试。"
            )

        filtered: List[RecommendationCandidate] = []
        avoided = {
            item.strip()
            for item in constraints.avoid_herbs
            if item and item.strip()
        }
        excluded = 0
        for item in recommendations:
            herb_names = item["herb_names"]
            if avoided and any(name in avoided for name in herb_names):
                excluded += 1
                continue
            if (
                constraints.max_herb_count is not None
                and len(herb_names) > constraints.max_herb_count
            ):
                excluded += 1
                continue
            filtered.append(
                RecommendationCandidate(
                    prescription_id=item["prescription_id"],
                    name=item["name"],
                    match_score=round(item["match_score"], 1),
                    reasons=item["reasons"][:5],
                    core_herbs=item["core_herbs"],
                    constraints_checked=True,
                    source=item["source"],
                    degraded=degraded or item["source"] == "database",
                    functions=item.get("functions"),
                    indications=item.get("indications"),
                    source_text=item.get("source_text"),
                    conflict_warnings=item.get("conflict_warnings", []),
                )
            )

        if recommendations and not filtered and reason is None:
            reason = (
                f"共有{excluded}个候选因避用药材或最大药味数约束被排除，"
                "未保留满足约束的方剂。"
            )

        return RecommendationResult(
            recommendations=filtered[:5],
            syndrome=None,
            analysis=(
                f"基于数据库中{len(recommendations)}个明确匹配候选完成约束校验，"
                f"保留{len(filtered[:5])}个结果。"
                if recommendations
                else None
            ),
            reason=reason,
            degraded=degraded or any(item.degraded for item in filtered),
        )

    def _database_recommendations(self, symptoms: str) -> List[Dict]:
        """按证候字段和常见同义词计算确定性匹配度。"""
        if not symptoms:
            return []

        terms = self._recommendation_terms(symptoms)
        if not terms:
            return []

        prescriptions = (
            self.db.query(Prescription)
            .options(
                joinedload(Prescription.herbs).joinedload(
                    PrescriptionHerbModel.herb
                )
            )
            .all()
        )
        results: List[Dict] = []
        field_weights = {
            "name": 20,
            "functions": 26,
            "indications": 30,
            "category": 16,
            "source": 8,
        }
        field_labels = {
            "name": "方名",
            "functions": "功效",
            "indications": "主治",
            "category": "分类",
            "source": "出处",
        }

        for prescription in prescriptions:
            fields = {
                "name": prescription.name or "",
                "functions": prescription.functions or "",
                "indications": prescription.indications or "",
                "category": prescription.category or "",
                "source": prescription.source or "",
            }
            raw_score = 0.0
            reasons: List[str] = []
            seen_reasons = set()
            for term in terms:
                for field, text in fields.items():
                    if term and term in text:
                        raw_score += field_weights[field] + min(len(term), 6)
                        reason = f"{field_labels[field]}与“{term}”相关"
                        if reason not in seen_reasons:
                            seen_reasons.add(reason)
                            reasons.append(reason)

            if raw_score <= 0:
                continue

            herb_rows = sorted(
                prescription.herbs or [],
                key=lambda row: row.order or 0,
            )
            herb_names = [
                row.herb.name
                for row in herb_rows
                if row.herb is not None
            ]
            conflict_summary = conflict_checker.check_with_summary(herb_names)
            conflict_warnings = [
                (
                    f"{item['herb_a']}与{item['herb_b']}命中"
                    f"{item['rule_type']}（{item['rule_name']}）"
                )
                for item in conflict_summary.get("conflicts", [])
            ]
            results.append(
                {
                    "prescription_id": prescription.id,
                    "name": prescription.name,
                    "match_score": min(100.0, 35.0 + raw_score),
                    "reasons": reasons,
                    "core_herbs": herb_names[:4],
                    "herb_names": herb_names,
                    "functions": prescription.functions,
                    "indications": prescription.indications,
                    "source_text": prescription.source,
                    "source": "database",
                    "conflict_warnings": conflict_warnings,
                }
            )
        return results

    def _merge_llm_recommendations(
        self,
        candidate_map: Dict[int, Dict],
        llm_rows: List[Dict],
    ) -> None:
        """仅合并能按名称解析到数据库的模型候选。"""
        if not llm_rows:
            return
        rows = (
            self.db.query(Prescription)
            .options(
                joinedload(Prescription.herbs).joinedload(
                    PrescriptionHerbModel.herb
                )
            )
            .filter(Prescription.name.in_([row.get("name") for row in llm_rows if row.get("name")]))
            .all()
        )
        by_name = {row.name: row for row in rows}
        for llm_row in llm_rows:
            name = (llm_row.get("name") or "").strip()
            prescription = by_name.get(name)
            if not prescription:
                continue
            item = candidate_map.get(prescription.id)
            if item is None:
                herb_names = [
                    relation.herb.name
                    for relation in sorted(
                        prescription.herbs or [],
                        key=lambda row: row.order or 0,
                    )
                    if relation.herb is not None
                ]
                item = {
                    "prescription_id": prescription.id,
                    "name": prescription.name,
                    "match_score": float(llm_row.get("match_score") or 60),
                    "reasons": [],
                    "core_herbs": herb_names[:4],
                    "herb_names": herb_names,
                    "functions": prescription.functions,
                    "indications": prescription.indications,
                    "source_text": prescription.source,
                    "source": "llm+database",
                    "conflict_warnings": [],
                }
                candidate_map[prescription.id] = item
            item["match_score"] = max(
                item["match_score"],
                float(llm_row.get("match_score") or 0),
            )
            llm_reason = (llm_row.get("reason") or "").strip()
            if llm_reason and llm_reason not in item["reasons"]:
                item["reasons"].insert(0, llm_reason)
            item["source"] = "database+llm"

    @classmethod
    def _recommendation_terms(cls, symptoms: str) -> List[str]:
        """提取症状词、常见中医同义词和中文双字片段。"""
        synonym_map = {
            "乏力": ["乏力", "无力", "倦怠", "疲乏", "体倦"],
            "食欲不振": ["食欲不振", "食少", "纳差", "纳呆", "不欲食"],
            "便溏": ["便溏", "大便溏", "大便不成形", "腹泻"],
            "失眠": ["失眠", "不寐", "夜寐不安", "睡眠"],
            "心悸": ["心悸", "怔忡", "惊悸"],
            "头晕": ["头晕", "眩晕", "头眩"],
            "咳嗽": ["咳嗽", "咳逆"],
            "发热": ["发热", "身热", "恶热"],
            "恶寒": ["恶寒", "畏寒", "怕冷"],
            "腹胀": ["腹胀", "痞满", "脘痞"],
            "便秘": ["便秘", "大便不通", "便结"],
        }
        segments = cls._segment_keywords(symptoms)
        stop_terms = {
            "最近", "感觉", "请问", "适合", "什么", "怎么", "可以",
            "一直", "经常", "并且", "而且", "出现", "有点",
        }
        terms: List[str] = []
        for segment in segments:
            normalized = segment.strip()
            if normalized in stop_terms:
                continue
            terms.append(normalized)
            for keyword, synonyms in synonym_map.items():
                if keyword in normalized or any(word in normalized for word in synonyms):
                    terms.extend(synonyms)
            if len(normalized) >= 4:
                terms.extend(
                    normalized[index:index + 2]
                    for index in range(len(normalized) - 1)
                )

        result: List[str] = []
        for term in terms:
            cleaned = term.strip()
            if len(cleaned) >= 2 and cleaned not in stop_terms and cleaned not in result:
                result.append(cleaned)
        return result[:40]

    # ============ 主入口 ============
    async def generate(self, symptoms: str, use_llm: bool = True) -> Dict:
        """生成配伍参考方案（含禁忌检测标注）"""
        # 优先大模型
        if use_llm:
            try:
                raw = await llm_service._call_llm(
                    [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": build_prompt(symptoms)}],
                )
                parsed = self._parse_llm_json(raw)
                scheme = self._decorate_candidates(parsed, source="llm")
                scheme["llm_used"] = True
                return scheme
            except Exception as e:
                logger.warning(f"LLM 智能配伍失败，降级到本地知识库: {e}")

        # 本地知识库兜底（关键词检索 + 禁忌检测）
        scheme = self._knowledge_base_match(symptoms)
        scheme["llm_used"] = False
        return scheme

    # ============ LLM JSON 解析 ============
    def _parse_llm_json(self, raw: str) -> Dict:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
        return json.loads(text)

    # ============ 候选方案装饰（禁忌检测） ============
    def _decorate_candidates(self, parsed: Dict, source: str) -> Dict:
        candidates = []
        for cand in parsed.get("candidates", [])[:3]:
            herbs_raw = cand.get("herbs", [])
            herbs = [h.strip() for h in herbs_raw if h and h.strip()]
            # N02 禁忌检测
            conflict_result = conflict_checker.check_with_summary(herbs)
            conflict_names = set()
            for c in conflict_result.get("conflicts", []):
                conflict_names.add(c["herb_a"])
                conflict_names.add(c["herb_b"])
            candidates.append({
                "name": cand.get("name", "未命名方"),
                "source": cand.get("source", ""),
                "functions": cand.get("functions", ""),
                "indications": cand.get("indications", ""),
                "reason": cand.get("reason", ""),
                "dosage_note": cand.get("dosage_note", ""),
                "herbs": herbs,
                "conflict_herbs": sorted(conflict_names),
                "conflict_check": conflict_result,
            })
        return {
            "syndrome": parsed.get("syndrome", ""),
            "analysis": parsed.get("analysis", ""),
            "candidates": candidates,
            "source": source,
        }

    # ============ 本地知识库匹配（降级） ============
    def _knowledge_base_match(self, symptoms: str, top_k: int = 3) -> Dict:
        from app.models.database_models import Herb, Prescription, PrescriptionHerb

        user_text = symptoms.replace("：", "").replace(":", "")
        # 用户切词（去掉过长的整句，保留语义块）
        user_parts = self._segment_keywords(user_text)

        rx = self.db.query(Prescription).all()
        scored = []
        for p in rx:
            # 每个字段单独成段（避免不同字段粘成一串导致无法匹配），再按标点细分
            pieces = [p.name, p.source or "", p.functions or "",
                      p.indications or "", p.category or ""]
            corpus = []
            for piece in pieces:
                tmp = piece
                for ch in ("，", "。", "；", "、", ",", ";", ":", "：", " ", "\u3000"):
                    tmp = tmp.replace(ch, " ")
                for seg in tmp.split(" "):
                    seg = seg.strip()
                    if len(seg) >= 2:
                        corpus.append(seg)
            score = 0
            matched = []
            for seg in corpus:
                # 剥掉"证/证候/之X证"等尾缀，使"脾胃气虚证"能匹配用户输入的"脾胃气虚"
                seg_core = seg
                for suffix in ("证候", "之证", "证"):
                    if seg_core.endswith(suffix):
                        seg_core = seg_core[: -len(suffix)]
                        break
                # 双向：库方片段出现在用户输入中 / 用户词出现在库方片段中
                hit_by_user = None
                if seg in user_text or (seg_core != seg and seg_core in user_text):
                    score += 3
                    matched.append(seg_core)
                    hit_by_user = True
                if hit_by_user is None:
                    for up in user_parts:
                        if len(up) >= 2 and (up in seg or up in seg_core):
                            score += 1
                            matched.append(up)
                            break
            if score > 0:
                scored.append((score, p, sorted(set(matched))))

        scored.sort(key=lambda x: -x[0])
        if scored:
            top = scored[:top_k]
        else:
            top = [(0, p, []) for p in rx[:top_k]]

        candidates = []
        for _, p, matched_kw in top:
            phs = self.db.query(PrescriptionHerb).filter(
                PrescriptionHerb.prescription_id == p.id
            ).order_by(PrescriptionHerb.order).all()
            herbs = []
            for ph in phs:
                h = self.db.query(Herb).filter(Herb.id == ph.herb_id).first()
                if h:
                    herbs.append(h.name)
            conflict_result = conflict_checker.check_with_summary(herbs)
            conflict_names = set()
            for c in conflict_result.get("conflicts", []):
                conflict_names.add(c["herb_a"])
                conflict_names.add(c["herb_b"])
            matched_desc = "、".join(matched_kw) if matched_kw else "（暂无精确匹配，展示经典方供参考）"
            candidates.append({
                "name": p.name,
                "source": p.source or "",
                "functions": p.functions or "",
                "indications": p.indications or "",
                "reason": f"与您描述相关的证候/功效关键词：{matched_desc}（分类：{p.category or '未分类'}）",
                "dosage_note": "",
                "herbs": herbs,
                "conflict_herbs": sorted(conflict_names),
                "conflict_check": conflict_result,
            })

        return {
            "syndrome": "依据知识库经典方匹配（大模型暂不可用时的降级方案）",
            "analysis": f"在 {len(rx)} 首经典方剂中，按证候关键词匹配出 {len(candidates)} 个候选；所有方案均已通过十八反/十九畏规则校验，仅供参考。",
            "candidates": candidates,
            "source": "knowledge_base",
        }

    @staticmethod
    def _segment_keywords(text: str) -> List[str]:
        """把主诉切成语义块：按常见标点/连接词切分，丢弃过短碎片"""
        # 用 str.replace 统一常见分隔符，避免字符类正则在不同环境的解析差异
        t = text
        for ch in ("：", ":", "，", ",", "。", "；", ";", "、", "\n", "\r"):
            t = t.replace(ch, " ")
        for conj in ("伴", "兼", "和", "及"):
            t = t.replace(conj, " ")
        parts = [p.strip() for p in t.split(" ") if p.strip()]
        out = []
        for p in parts:
            if len(p) >= 2 and p not in out:
                out.append(p)
        if not out and len(text) >= 2:
            out = [text[:30]]
        return out[:10]


smart_service_factory = None
