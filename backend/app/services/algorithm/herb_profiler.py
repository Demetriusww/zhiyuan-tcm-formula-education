# -*- coding: utf-8 -*-
"""
药材性味归经解析器 —— 把非结构化的性味/归经文本解析为可量化的维度向量
例: "辛、微苦，温"  →  flavors={辛, 苦}  thermal=温
     "归肺、膀胱经" →  meridians={肺, 膀胱}
纯确定性逻辑，无任何外部依赖。
"""
import re
from typing import Dict, List, Set, Tuple

# 五性档位：文本表述 -> 标准 5 档
THERMAL_MAP: Dict[str, str] = {
    "大热": "热", "热": "热",
    "温": "温", "微温": "温",
    "平": "平",
    "凉": "凉", "微寒": "凉",  # 微寒偏凉
    "寒": "寒", "大寒": "寒",
}

# 五味(含涩、淡两个补充味)
FLAVOR_SET: List[str] = ["酸", "苦", "甘", "辛", "咸", "淡", "涩"]

# 十二归经
MERIDIAN_SET: List[str] = [
    "心", "肝", "脾", "肺", "肾",
    "胃", "胆", "大肠", "小肠", "膀胱", "三焦", "心包",
]

# 味的前缀(微/大/炒等)，解析时剥掉只留核心味字
_FLAVOR_PREFIX = ("微", "大", "炒", "焦", "盐")


def parse_thermal_flavor(property_text: str) -> Tuple[str, Set[str]]:
    """
    解析 "辛、微苦，温" / "甘，大寒" / "咸，平；有毒" 这类性味串
    返回 (五性档位, 味集合)；无法识别时 thermal="" / flavors=空集
    规则：以中文逗号(,，)为界，前面是味、后面是性；
          若整串不含逗号，尝试直接识别味/性关键词。
    """
    if not property_text:
        return "", set()
    text = property_text.strip()
    # 去掉 "；有毒""(有毒)" 等杂质
    text = re.split(r"[；;（(]", text)[0].strip()

    parts = re.split(r"[，,]", text)
    thermal = ""
    flavors: Set[str] = set()

    if len(parts) >= 2:
        # 逗号前是味(可能多个，用、分隔)，逗号后是性
        flavor_part, thermal_part = parts[0], parts[-1]
        for token in re.split(r"[、]|[\s]+", flavor_part):
            f = _core_flavor(token)
            if f in FLAVOR_SET:
                flavors.add(f)
        thermal = _core_thermal(thermal_part)
        # 若逗号后也是味(如 "辛、甘" 无性)，再尝试从第二段抓性
        if not thermal:
            for token in re.split(r"[、]|[\s]+", thermal_part):
                if _core_flavor(token) in FLAVOR_SET:
                    flavors.add(_core_flavor(token))
        return thermal, flavors

    # 无逗号：整串可能是 "平" / "辛" / "甘、温"之类，逐 token 识别
    for token in re.split(r"[、]|[\s]+", text):
        f = _core_flavor(token)
        if f in FLAVOR_SET:
            flavors.add(f)
        t = _core_thermal(token)
        if t and not thermal:
            thermal = t
    return thermal, flavors


def _core_flavor(token: str) -> str:
    """取 token 的核心味字："微苦"→苦；"辛"→辛；无匹配返回空"""
    if not token:
        return ""
    for pre in _FLAVOR_PREFIX:
        if token.startswith(pre) and len(token) > 1:
            token = token[len(pre):]
            break
    return token if token in FLAVOR_SET else ""


def _core_thermal(token: str) -> str:
    """"大寒/寒/微温/平..." → 五性档位；无匹配返回空"""
    token = token.strip()
    if not token:
        return ""
    # 先长后短匹配（大寒、微温优先）
    for key in ("大热", "大寒", "微温", "微寒", "温", "凉", "平", "寒", "热"):
        if key in token:
            return THERMAL_MAP[key]
    return ""


def parse_meridians(meridian_text: str) -> Set[str]:
    """解析 "归肺、膀胱经" / "入肝、肾经" → {肺, 膀胱}"""
    if not meridian_text:
        return set()
    text = meridian_text.replace("归", "").replace("入", "").replace("经", "")
    result: Set[str] = set()
    for token in re.split(r"[、，,/\s]+", text):
        token = token.strip()
        if not token:
            continue
        # 处理 "手太阴肺" 这类：取最后那个脏/腑字
        hit = ""
        for m in MERIDIAN_SET:
            if m in token:
                hit = m
                break
        if hit:
            result.add(hit)
    return result


def herb_profile(property_text: str, meridian_text: str) -> Dict:
    """
    单味药材的可量化画像: {thermal, flavors(list), meridians(list)}
    供方剂指纹聚合使用
    """
    thermal, flavors = parse_thermal_flavor(property_text)
    mers = parse_meridians(meridian_text)
    return {
        "thermal": thermal,
        "flavors": sorted(flavors),
        "meridians": sorted(mers),
    }


if __name__ == "__main__":
    # 自测
    cases = [
        ("辛、微苦，温", "归肺、膀胱经"),
        ("甘、辛，大寒", "归肺、胃经"),
        ("甘，平", "归心、肺、脾、胃经"),
        ("辛、甘，大热；有毒", "归心、肾、脾经"),
        ("苦，寒", "归心、肝、胃、大肠经"),
        ("甘、微苦，微温", "归脾、肺经"),
    ]
    for p, m in cases:
        print(f"{p!r:24} + {m!r:22} → {herb_profile(p, m)}")
