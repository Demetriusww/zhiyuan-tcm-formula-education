# -*- coding: utf-8 -*-
"""
方剂相似度服务 —— 输入一个方剂，返回库内 TopN 相似方剂
相似度 = 0.55 × 组成药材 Jaccard + 0.45 × 性味归经指纹向量余弦相似度
纯确定性算法，不依赖大模型。数据来源：方剂-药材关联表 + 药材性味归经字段。
"""
import logging
from typing import Dict, List, Optional

from app.services.algorithm.herb_profiler import FLAVOR_SET, MERIDIAN_SET, \
    THERMAL_MAP, herb_profile

logger = logging.getLogger("tcm_platform.similarity")

# 五性档位顺序
THERMAL_ORDER = ["寒", "凉", "平", "温", "热"]

# 相似度融合权重
W_JACCARD = 0.55
W_COSINE = 0.45


class PrescriptionSimilarityService:
    """方剂相似度服务"""

    def __init__(self, db):
        self.db = db
        self._herb_meta: Dict[str, Dict] = {}   # herb_name -> {property, meridian}
        self._prescriptions: List[Dict] = []     # 全部方剂基本信息 + herb_names
        self._profiles: Dict[int, Dict] = {}     # prescription_id -> 指纹
        self._loaded = False

    # ---------- 数据装载 ----------
    def _ensure_loaded(self):
        if self._loaded:
            return
        from app.models.database_models import Herb, Prescription, PrescriptionHerb

        # 1) 药材属性映射（一次加载，避免 N+1）
        for h in self.db.query(Herb).all():
            self._herb_meta[h.name] = {
                "property": h.property or "",
                "meridian": h.meridians or "",
            }

        # 2) 全部方剂（含组成药材名）
        ph_rows = self.db.query(
            PrescriptionHerb.prescription_id, PrescriptionHerb.herb_id
        ).all()
        herb_id2name = {h.id: h.name for h in self.db.query(Herb).all()}
        pres_id2herb_ids: Dict[int, List[int]] = {}
        for pid, hid in ph_rows:
            pres_id2herb_ids.setdefault(pid, []).append(hid)

        for p in self.db.query(Prescription).all():
            hids = pres_id2herb_ids.get(p.id, [])
            names = []
            for hid in hids:
                nm = herb_id2name.get(hid)
                if nm:
                    names.append(nm)
            self._prescriptions.append({
                "id": p.id, "name": p.name, "category": p.category or "",
                "source": p.source or "", "functions": p.functions or "",
                "indications": p.indications or "",
                "herb_names": list(dict.fromkeys(names)),  # 去重保序
            })

        # 3) 指纹
        for p in self._prescriptions:
            self._profiles[p["id"]] = self._build_profile(p["herb_names"])

        self._loaded = True
        logger.info(f"相似度服务装载: {len(self._prescriptions)} 方 / {len(self._herb_meta)} 药")

    # ---------- 指纹 ----------
    def _build_profile(self, herb_names: List[str]) -> Dict:
        """方剂指纹：聚合组成药材的五性/五味/归经频次"""
        thermal = {t: 0 for t in THERMAL_ORDER}
        flavor = {f: 0 for f in FLAVOR_SET}
        meridian = {m: 0 for m in MERIDIAN_SET}
        for hn in herb_names:
            meta = self._herb_meta.get(hn)
            if not meta:
                continue
            prof = herb_profile(meta["property"], meta["meridian"])
            if prof["thermal"]:
                thermal[prof["thermal"]] += 1
            for f in prof["flavors"]:
                flavor[f] += 1
            for m in prof["meridians"]:
                meridian[m] += 1
        return {
            "herb_count": len(herb_names),
            "thermal": thermal,
            "flavor": flavor,
            "meridian": meridian,
        }

    @staticmethod
    def _vectorize(profile: Dict) -> List[float]:
        """指纹 -> 归一向量（各维度组内按占比归一，消除方剂大小影响）"""
        vec: List[float] = []
        for key in ("thermal", "flavor", "meridian"):
            counts = profile[key]
            total = sum(counts.values())
            if total == 0:
                vec.extend([0.0] * len(counts))
            else:
                vec.extend(c / total for c in counts.values())
        return vec

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    @staticmethod
    def _jaccard(a: List[str], b: List[str]) -> float:
        sa, sb = set(a), set(b)
        union = sa | sb
        if not union:
            return 0.0
        return len(sa & sb) / len(union)

    # ---------- 对外查询 ----------
    def similar(self, name: str = None, prescription_id: int = None,
                top_k: int = 5, min_overlap: int = 0) -> Optional[Dict]:
        """
        返回指定方剂的 TopN 相似方剂
        name / prescription_id 二选一；返回 None 表示方剂不存在
        """
        self._ensure_loaded()
        base = None
        for p in self._prescriptions:
            if (name and p["name"] == name) or \
               (prescription_id and p["id"] == prescription_id):
                base = p
                break
        if not base:
            return None

        base_vec = self._vectorize(self._profiles[base["id"]])
        base_set = set(base["herb_names"])

        scored = []
        for p in self._prescriptions:
            if p["id"] == base["id"]:
                continue
            jac = self._jaccard(base_set, p["herb_names"])
            overlap = len(base_set & set(p["herb_names"]))
            if overlap < min_overlap:
                continue
            cos = self._cosine(base_vec, self._vectorize(self._profiles[p["id"]]))
            score = W_JACCARD * jac + W_COSINE * cos
            scored.append((score, jac, cos, overlap, p))

        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]

        similar_list = []
        for score, jac, cos, overlap, p in top:
            similar_list.append({
                "id": p["id"], "name": p["name"],
                "category": p["category"], "source": p["source"],
                "functions": p["functions"], "indications": p["indications"],
                "herb_count": len(p["herb_names"]),
                "herb_names": p["herb_names"],
                "score": round(score, 4),
                "jaccard": round(jac, 4),
                "cosine": round(cos, 4),
                "overlap_count": overlap,
                "overlap_herbs": sorted(base_set & set(p["herb_names"])),
                "profile": self._profiles[p["id"]],
            })

        return {
            "base": {
                "id": base["id"], "name": base["name"],
                "category": base["category"], "source": base["source"],
                "functions": base["functions"], "indications": base["indications"],
                "herb_count": len(base["herb_names"]),
                "herb_names": base["herb_names"],
                "profile": self._profiles[base["id"]],
            },
            "similar": similar_list,
            "algo": {
                "note": "score = 0.55×组成Jaccard + 0.45×性味归经向量余弦",
                "w_jaccard": W_JACCARD, "w_cosine": W_COSINE,
            },
        }


# 模块级便捷入口（每次请求由依赖注入 DB）
def get_similarity_service(db) -> PrescriptionSimilarityService:
    return PrescriptionSimilarityService(db)


if __name__ == "__main__":
    # 直接自测
    from app.core.database import SessionLocal
    db = SessionLocal()
    svc = PrescriptionSimilarityService(db)
    r = svc.similar(name="六味地黄丸", top_k=4)
    if r:
        print("基准方:", r["base"]["name"], "| 药味数:", r["base"]["herb_count"])
        print("指纹·归经:", r["base"]["profile"]["meridian"])
        print("指纹·药性:", r["base"]["profile"]["thermal"])
        print()
        for s in r["similar"]:
            print(f"  {s['name']:<10} score={s['score']:.3f} "
                  f"jaccard={s['jaccard']:.3f} cos={s['cosine']:.3f} "
                  f"共药{s['overlap_count']} {s['overlap_herbs']}")
    db.close()
