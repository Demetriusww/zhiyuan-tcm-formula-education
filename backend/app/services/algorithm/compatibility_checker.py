# -*- coding: utf-8 -*-
"""
配伍禁忌检测算法（自研、确定性规则引擎，不依赖大模型）

功能：接收一组药材名称，依据十八反、十九畏规则检测冲突，
输出：冲突对、规则类型、所属规则组、风险等级、建议。
"""
from __future__ import annotations

from typing import List, Dict, Any

from app.services.algorithm.conflict_rules import (
    EIGHTEEN_OPPOSITES,
    NINETEEN_FEARS,
)


# 常用炮制/别名归一（只用于增强匹配，不强制要求收录）
ALIAS_NORM = {
    "制附片": "附子", "黑附片": "附子", "白附片": "附子",
    "法夏": "半夏", "炙半夏": "半夏",
    "全栝楼": "瓜蒌", "栝楼": "瓜蒌",
    "象贝": "浙贝母",
    "赤石脂": "赤石脂",
    "元参": "玄参", "玄胡索": "延胡索",
    "桂": "肉桂",
}


class ConflictResult:
    """一条冲突检测结果"""

    def __init__(self, herb_a: str, herb_b: str, rule_type: str,
                 rule_name: str, description: str, tip: str = "",
                 level: str = "high"):
        self.herb_a = herb_a
        self.herb_b = herb_b
        self.rule_type = rule_type          # 十八反 / 十九畏
        self.rule_name = rule_name          # 例如：乌头类 × 半夏类
        self.description = description
        self.tip = tip
        self.level = level                  # high / warning

    def to_dict(self) -> Dict[str, Any]:
        return {
            "herb_a": self.herb_a,
            "herb_b": self.herb_b,
            "rule_type": self.rule_type,
            "rule_name": self.rule_name,
            "description": self.description,
            "tip": self.tip,
            "level": self.level,
        }


class CompatibilityChecker:
    """配伍禁忌检测器"""

    def __init__(self):
        # 预处理：建立 药名 -> [(对方, 规则组, 类型)] 正向索引，O(1) 查冲突
        self._index: Dict[str, List[tuple]] = {}
        self._build_index()

    def _build_index(self):
        # 十八反
        for group in EIGHTEEN_OPPOSITES:
            members = [self._norm(m) for m in group["members"]]
            opposes = [self._norm(o) for o in group["opposes"]]
            for m in members:
                for o in opposes:
                    self._add(m, o, "十八反", group)
        # 十九畏
        for fear in NINETEEN_FEARS:
            for a in fear["a"]:
                for b in fear["b"]:
                    self._add(self._norm(a), self._norm(b), "十九畏", fear)

    def _add(self, a: str, b: str, rule_type: str, group: dict):
        """双向建立索引，确保任意输入顺序都能命中"""
        self._index.setdefault(a, []).append((b, rule_type, group))
        self._index.setdefault(b, []).append((a, rule_type, group))

    @staticmethod
    def _norm(name: str) -> str:
        return ALIAS_NORM.get(name, name)

    def check(self, herbs: List[str]) -> List[Dict[str, Any]]:
        """
        检测药材列表中的配伍禁忌。

        Args:
            herbs: 药材名称列表，如 ["人参", "半夏", "附子"]
        Returns:
            冲突结果列表（可能为空）。顺序稳定，去重。
        """
        if not herbs:
            return []

        # 药材名 -> 标准化名（保留原名展示）
        seen = set()
        unique_herbs: List[str] = []
        for h in herbs:
            h = (h or "").strip()
            if h and h not in seen:
                seen.add(h)
                unique_herbs.append(h)

        results: List[Dict[str, Any]] = []
        visited_pairs = set()

        for i, herb in enumerate(unique_herbs):
            norm = self._norm(herb)
            for j in range(i + 1, len(unique_herbs)):
                other = unique_herbs[j]
                other_norm = self._norm(other)
                for target, rule_type, group in self._index.get(norm, []):
                    if target == other_norm:
                        pair = tuple(sorted([herb, other]))
                        if pair in visited_pairs:
                            continue
                        visited_pairs.add(pair)
                        level = "high" if rule_type == "十八反" else "warning"
                        results.append(ConflictResult(
                            herb_a=herb,
                            herb_b=other,
                            rule_type=rule_type,
                            rule_name=group.get("group_name") or
                            (group.get("description") or "相畏禁忌"),
                            description=group.get("description", ""),
                            tip=group.get("tip", ""),
                            level=level,
                        ).to_dict())

        return results

    def check_with_summary(self, herbs: List[str]) -> Dict[str, Any]:
        """检测并附带汇总信息，便于前端展示"""
        conflicts = self.check(herbs)
        by_type: Dict[str, int] = {}
        for c in conflicts:
            by_type[c["rule_type"]] = by_type.get(c["rule_type"], 0) + 1
        return {
            "safe": len(conflicts) == 0,
            "conflict_count": len(conflicts),
            "by_type": by_type,
            "conflicts": conflicts,
            "checked_herbs": len(set(h.strip() for h in herbs if h and h.strip())),
        }


checker = CompatibilityChecker()

if __name__ == "__main__":
    # 快速自测
    cases = [
        ["人参", "白术", "茯苓", "甘草"],
        ["人参", "半夏", "附子", "甘草"],          # 附子×半夏 → 十八反
        ["甘草", "海藻"],                          # 甘草×海藻 → 十八反
        ["人参", "五灵脂"],                        # 十九畏
        ["芒硝", "三棱"],                          # 牙硝畏三棱
    ]
    for c in cases:
        r = checker.check_with_summary(c)
        print(f"{'、'.join(c)} => 冲突{r['conflict_count']}条")
        for x in r["conflicts"]:
            print(f"   [{x['rule_type']}] {x['herb_a']} × {x['herb_b']} | {x['description']}")
