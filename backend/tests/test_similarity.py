# -*- coding: utf-8 -*-
"""
方剂相似度算法测试
- 纯函数：性味归经解析 / Jaccard / 余弦
- 集成：真实库中方剂 TopN（六味地黄丸 → 地黄丸家族）
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.services.algorithm.herb_profiler import (
    parse_thermal_flavor, parse_meridians, herb_profile,
)
from app.services.algorithm.prescription_similarity import (
    PrescriptionSimilarityService,
)
from app.services.algorithm import prescription_similarity as ps

# ---------- 纯函数：性味归经解析 ----------

class TestHerbProfiler:
    def test_typical_thermal_flavor(self):
        t, f = parse_thermal_flavor("辛、微苦，温")
        assert t == "温"
        assert f == {"辛", "苦"}

    def test_dahan_to_han(self):
        t, _ = parse_thermal_flavor("甘、辛，大寒")
        assert t == "寒"

    def test_plain_gan_ping(self):
        t, f = parse_thermal_flavor("甘，平")
        assert t == "平"
        assert f == {"甘"}

    def test_weihan_to_liang(self):
        t, _ = parse_thermal_flavor("甘、微苦，微温")
        assert t == "温"

    def test_poison_suffix_ignored(self):
        t, f = parse_thermal_flavor("辛、甘，大热；有毒")
        assert t == "热"
        assert f == {"辛", "甘"}

    def test_meridians_parse(self):
        m = parse_meridians("归肺、膀胱经")
        assert m == {"肺", "膀胱"}
        m2 = parse_meridians("归心、肝、脾经")
        assert m2 == {"心", "肝", "脾"}

    def test_herb_profile_integration(self):
        p = herb_profile("甘，平", "归心、肺、脾、胃经")
        assert p["thermal"] == "平"
        assert p["flavors"] == ["甘"]
        assert set(p["meridians"]) == {"心", "肺", "脾", "胃"}


# ---------- 纯函数：相似度 ----------

class TestSimilarityMath:
    def test_jaccard(self):
        svc = PrescriptionSimilarityService.__new__(PrescriptionSimilarityService)
        assert svc._jaccard(["a", "b", "c"], ["a", "b", "d"]) == 2 / 4
        assert svc._jaccard([], []) == 0.0

    def test_cosine(self):
        assert ps.PrescriptionSimilarityService._cosine([1, 0], [1, 0]) == 1.0
        assert ps.PrescriptionSimilarityService._cosine([1, 0], [0, 1]) == 0.0
        assert ps.PrescriptionSimilarityService._cosine([0, 0], [1, 1]) == 0.0


# ---------- 集成：真实库 ----------

@pytest.fixture(scope="module")
def svc():
    from app.core.database import SessionLocal
    db = SessionLocal()
    s = PrescriptionSimilarityService(db)
    s._ensure_loaded()
    yield s
    db.close()


class TestSimilarityIntegration:
    def test_six_ingredient_top_similar(self, svc):
        r = svc.similar(name="六味地黄丸", top_k=5)
        assert r is not None
        names = [x["name"] for x in r["similar"]]
        # 地黄丸家族应出现在最相似列表
        assert any("地黄" in n for n in names), f"未命中地黄丸家族: {names}"
        # 与杞菊/麦味地黄丸共药 6 味（同组成加减）
        top = r["similar"][0]
        assert top["overlap_count"] >= 5
        assert top["score"] > 0.7

    def test_profile_dimensions(self, svc):
        r = svc.similar(name="四君子汤", top_k=3)
        prof = r["base"]["profile"]
        # 三维度齐全
        assert set(prof["thermal"].keys()) == {"寒", "凉", "平", "温", "热"}
        assert len(prof["meridian"]) == 12
        assert prof["herb_count"] == 4

    def test_not_found(self, svc):
        assert svc.similar(name="不存在的方剂xx") is None

    def test_min_overlap_filter(self, svc):
        r = svc.similar(name="四君子汤", top_k=5, min_overlap=2)
        for x in r["similar"]:
            assert x["overlap_count"] >= 2
