# -*- coding: utf-8 -*-
"""
平台统计与知识图谱数据服务 —— 为可视化大页提供数据
- overview: 药材频次 / 方剂分类 / 药性 / 归经 / 药味 分布 + 基础总数
- graph: 药材-方剂二部图（力导向图数据），支持 全量 / 高频TopN / 按分类
纯确定性聚合，直接从数据库现算（数据规模小，毫秒级返回）。
"""
import logging
from collections import Counter
from typing import Dict, List, Optional

from app.services.algorithm.herb_profiler import (
    FLAVOR_SET, MERIDIAN_SET, herb_profile,
)

# 五性档位顺序（与 herb_profiler.THERMAL_MAP 归一后一致）
THERMAL_ORDER = ["寒", "凉", "平", "温", "热"]

logger = logging.getLogger("tcm_platform.stats")


class StatsService:
    """统计与图谱数据服务"""

    def __init__(self, db):
        self.db = db

    # ---------- 基础加载 ----------
    def _load_all(self) -> Dict:
        """一次加载 药材(属性) + 方剂(含组成、分类) + 关联，返回内部结构"""
        from app.models.database_models import Herb, Prescription, PrescriptionHerb

        herb_rows = self.db.query(Herb).all()
        herbs = {
            h.name: {"property": h.property or "", "meridian": h.meridians or ""}
            for h in herb_rows
        }
        herb_id2name = {h.id: h.name for h in herb_rows}

        ph = self.db.query(PrescriptionHerb.prescription_id, PrescriptionHerb.herb_id).all()
        pres2hids: Dict[int, List[int]] = {}
        for pid, hid in ph:
            pres2hids.setdefault(pid, []).append(hid)

        prescriptions = []
        for p in self.db.query(Prescription).all():
            hids = pres2hids.get(p.id, [])
            names = []
            for hid in hids:
                nm = herb_id2name.get(hid)
                if nm:
                    names.append(nm)
            prescriptions.append({
                "id": p.id, "name": p.name, "category": p.category or "未分类",
                "source": p.source or "", "herb_names": list(dict.fromkeys(names)),
            })
        return {"herbs": herbs, "prescriptions": prescriptions}

    # ---------- 概览统计 ----------
    def overview(self) -> Dict:
        data = self._load_all()
        herbs = data["herbs"]
        rx = data["prescriptions"]

        # 基础总数
        totals = {
            "herbs": len(herbs),
            "prescriptions": len(rx),
            "links": sum(len(p["herb_names"]) for p in rx),
            "categories": len({p["category"] for p in rx}),
        }
        avg = round(totals["links"] / totals["prescriptions"], 1) if rx else 0

        # 药材使用频次（出现于多少方）
        herb_freq = Counter()
        for p in rx:
            for hn in p["herb_names"]:
                herb_freq[hn] += 1

        # 药性/归经/药味（按"每味药材一次"聚合，即药材属性分布）
        thermal_cnt = {t: 0 for t in THERMAL_ORDER}
        meridian_cnt = {m: 0 for m in MERIDIAN_SET}
        flavor_cnt = {f: 0 for f in FLAVOR_SET}
        for hn, meta in herbs.items():
            prof = herb_profile(meta["property"], meta["meridian"])
            if prof["thermal"]:
                thermal_cnt[prof["thermal"]] += 1
            for m in prof["meridians"]:
                meridian_cnt[m] += 1
            for f in prof["flavors"]:
                flavor_cnt[f] += 1

        # 方剂分类分布
        cat_cnt = Counter(p["category"] for p in rx)

        return {
            "totals": totals,
            "avg_herbs_per_prescription": avg,
            "herb_freq_top": [{"name": n, "count": c} for n, c in herb_freq.most_common(20)],
            "category_dist": [{"name": n, "count": c} for n, c in
                              sorted(cat_cnt.items(), key=lambda x: -x[1])],
            "thermal_dist": [{"name": n, "count": c} for n, c in thermal_cnt.items() if c > 0],
            "meridian_dist": [{"name": n, "count": c} for n, c in meridian_cnt.items() if c > 0],
            "flavor_dist": [{"name": n, "count": c} for n, c in flavor_cnt.items() if c > 0],
            "algo_note": (
                f"统计基于库内 {totals['herbs']} 味药材、"
                f"{totals['prescriptions']} 个方剂和 {totals['links']} 条关联实时计算"
            ),
        }

    # ---------- 图谱数据 ----------
    def graph(self, mode: str = "all", category: Optional[str] = None,
              top_n: int = 30) -> Dict:
        """
        药材-方剂 二部图（力导向图数据）
        mode:
          all      -> 全量（236 节点 / 742 边）
          top      -> 仅出现频次最高的 top_n 味药材及其所在方剂
          category -> 仅某分类（如 补益剂）的方剂及其药材
        """
        data = self._load_all()
        herbs = data["herbs"]
        rx = data["prescriptions"]

        herb_freq = Counter()
        for p in rx:
            for hn in p["herb_names"]:
                herb_freq[hn] += 1

        if mode == "category" and category:
            keep_rx = [p for p in rx if p["category"] == category]
            mode_note = f"方剂分类「{category}」子图"
        elif mode == "top":
            hot = {n for n, _ in herb_freq.most_common(top_n)}
            keep_rx = []
            for p in rx:
                used = [hn for hn in p["herb_names"] if hn in hot]
                if used:
                    keep_rx.append({**p, "herb_names": used})
            mode_note = f"高频药材 Top{top_n} 关联子图"
        else:
            keep_rx = rx
            mode_note = "全库知识图谱"

        # 组装节点与边
        rx_in = set()
        herb_in = set()
        edges = []
        for p in keep_rx:
            rx_in.add(p["name"])
            for hn in p["herb_names"]:
                herb_in.add(hn)
                edges.append({"source": f"p_{p['name']}", "target": f"h_{hn}"})

        nodes = []
        for p in rx:
            if p["name"] not in rx_in:
                continue
            degree = sum(1 for e in edges if e["source"] == f"p_{p['name']}")
            nodes.append({
                "id": f"p_{p['name']}", "name": p["name"], "type": "prescription",
                "category": p["category"], "source": p["source"],
                "degree": degree, "herb_count": len(p["herb_names"]),
            })
        for hn in herbs:
            if hn not in herb_in:
                continue
            nodes.append({
                "id": f"h_{hn}", "name": hn, "type": "herb",
                "degree": herb_freq[hn],
                "property": herbs[hn]["property"],
                "meridian": herbs[hn]["meridian"],
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "meta": {
                "mode_note": mode_note,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "herb_count": sum(1 for n in nodes if n["type"] == "herb"),
                "prescription_count": sum(1 for n in nodes if n["type"] == "prescription"),
                "categories": sorted({p["category"] for p in rx}),
            },
        }
