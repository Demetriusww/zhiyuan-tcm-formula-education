# -*- coding: utf-8 -*-
"""配伍禁忌检测算法单元测试"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.algorithm.compatibility_checker import CompatibilityChecker


def _has(result, herb_a, herb_b, rule_type=None):
    """判断结果中是否包含 (herb_a × herb_b) 冲突"""
    for c in result:
        pair = {c["herb_a"], c["herb_b"]}
        if pair == {herb_a, herb_b}:
            if rule_type is None or c["rule_type"] == rule_type:
                return True
    return False


def test_safe_prescription_no_conflict():
    """四君子汤（人参、白术、茯苓、甘草）应无冲突"""
    checker = CompatibilityChecker()
    result = checker.check(["人参", "白术", "茯苓", "甘草"])
    assert len(result) == 0


def test_fuzi_banxia_eighteen_opposites():
    """附子 × 半夏 → 十八反"""
    checker = CompatibilityChecker()
    result = checker.check(["人参", "半夏", "附子", "甘草"])
    assert len(result) == 1
    assert _has(result, "附子", "半夏", "十八反")


def test_order_irrelevant():
    """输入顺序不影响检测结果"""
    checker = CompatibilityChecker()
    r1 = checker.check(["半夏", "附子"])
    r2 = checker.check(["附子", "半夏"])
    assert len(r1) == 1 and len(r2) == 1


def test_gancao_haizao():
    """甘草 × 海藻 → 十八反"""
    checker = CompatibilityChecker()
    assert _has(checker.check(["甘草", "海藻"]), "甘草", "海藻", "十八反")


def test_renshen_wulingzhi_nineteen_fears():
    """人参 × 五灵脂 → 十九畏"""
    checker = CompatibilityChecker()
    assert _has(checker.check(["人参", "五灵脂"]), "人参", "五灵脂", "十九畏")


def test_mangxiao_sanleng():
    """芒硝 × 三棱 → 十九畏"""
    checker = CompatibilityChecker()
    assert _has(checker.check(["芒硝", "三棱"]), "芒硝", "三棱", "十九畏")


def test_processed_alias_herb():
    """炮制/别名药名也应命中：姜半夏(姜半夏在opposes) × 附子"""
    checker = CompatibilityChecker()
    assert _has(checker.check(["姜半夏", "制附子"]), "姜半夏", "制附子", "十八反")


def test_multiple_conflicts_and_summary():
    """多组冲突同时检出 + 汇总信息"""
    checker = CompatibilityChecker()
    summary = checker.check_with_summary(["半夏", "附子", "甘草", "海藻"])
    assert summary["safe"] is False
    assert summary["conflict_count"] == 2
    assert summary["by_type"]["十八反"] == 2
    assert summary["checked_herbs"] == 4


def test_empty_input():
    checker = CompatibilityChecker()
    assert checker.check([]) == []
    assert checker.check_with_summary([])["safe"] is True
