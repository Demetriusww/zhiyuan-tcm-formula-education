# -*- coding: utf-8 -*-
"""
药材图像识别服务 —— 上传图片 → 视觉大模型(Moonshot Kimi K2.6)识别药材名
→ 别名归一化匹配库内药材 → 存入识别记录表
视觉 provider 通过 VISION_* 环境变量配置(.env)，可无缝换成 qwen-vl 等 OpenAI 兼容视觉模型
"""
import base64
import json
import logging
from typing import Dict, List, Optional

import httpx

from app.core.config import settings
from app.models.database_models import Herb, RecognitionRecord

logger = logging.getLogger("tcm_platform.vision")

# 常见别名 → 库内标准药名（与 seed 归一化保持一致的精简版）
HERB_ALIAS = {
    "枸杞": "枸杞子", "枸杞果": "枸杞子", "杞子": "枸杞子",
    "生地": "地黄", "生地黄": "地黄", "干地黄": "地黄", "鲜生地": "地黄",
    "熟地": "熟地黄",
    "山萸肉": "山茱萸", "枣皮": "山茱萸",
    "淮山": "山药", "怀山药": "山药",
    "北芪": "黄芪", "绵芪": "黄芪",
    "元参": "玄参", "苦桔梗": "桔梗", "浙贝": "浙贝母",
    "火麻仁": "火麻仁", "麻仁": "火麻仁", "杏仁": "苦杏仁",
    "桂皮": "肉桂", "国老": "甘草", "炙草": "甘草",
    "红枣": "大枣", "大红枣": "大枣",
    "田七": "三七", "云苓": "茯苓",
}

PROMPT = (
    "你是中药材饮片识别专家。仔细观察图片中的中药材（饮片/果实/花/根茎等），"
    "输出其中药材的标准药名。要求：\n"
    "1) 只输出一个 JSON 对象，不要任何多余文字或解释：{\"herbs\":[{\"name\":\"标准药名\"}],\"note\":\"简短补充\"}\n"
    "2) 药名使用《中国药典》正名，例如：枸杞子、菊花、金银花、陈皮、甘草、黄芪、当归、茯苓、山楂、罗汉果、川芎、丹参；\n"
    "3) 若图片中无法确定是何种药材，herbs 输出空数组并在 note 说明；\n"
    "4) 若图中没有药材（如空白、风景），herbs 为空。"
)


class HerbVisionService:
    def __init__(self, db):
        self.db = db
        self._herb_names: List[str] = []
        self._herb_name2id: Dict[str, int] = {}
        self._herb_id2pinyin: Dict[int, str] = {}

    def _ensure_herbs(self):
        if not self._herb_names:
            for h in self.db.query(Herb).all():
                self._herb_names.append(h.name)
                self._herb_name2id[h.name] = h.id
                self._herb_id2pinyin[h.id] = h.pinyin or ""

    # ---------- 视觉模型调用 ----------
    async def _call_vision(self, image_b64: str) -> str:
        if not settings.VISION_API_KEY:
            raise RuntimeError("视觉 API Key 未配置（backend/.env 的 VISION_API_KEY）")
        payload = {
            "model": settings.VISION_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            }],
            "max_tokens": 600,
        }
        headers = {
            "Authorization": f"Bearer {settings.VISION_API_KEY}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=settings.VISION_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.VISION_API_BASE}/chat/completions",
                headers=headers, json=payload)
            resp.raise_for_status()
            result = resp.json()
        content = (result.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        return content

    # ---------- 名称归一化匹配 ----------
    def _match(self, name: str) -> Optional[Dict]:
        """尝试把模型给出的药名匹配到库内药材（命中返回含 herb_id 与 pinyin，pinyin 供 ESP32 OLED 显示）"""
        self._ensure_herbs()
        n = (name or "").strip()
        if not n:
            return None

        def hit(std: str) -> Dict:
            return {"name": std, "herb_id": self._herb_name2id[std],
                    "pinyin": self._herb_id2pinyin.get(self._herb_name2id[std], "")}

        # 1) 别名
        if n in HERB_ALIAS:
            std = HERB_ALIAS[n]
            if std in self._herb_name2id:
                return hit(std)
        # 2) 直接命中
        if n in self._herb_name2id:
            return hit(n)
        # 3) 双向子串
        for std in self._herb_names:
            if (len(n) >= 2 and n in std) or (len(std) >= 2 and std in n):
                return hit(std)
        return None

    @staticmethod
    def _parse_herbs(raw: str) -> List[str]:
        """从模型返回文本抽取药名列表（容忍 ```json 代码块 / 多余文字）"""
        text = (raw or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        names: List[str] = []
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                obj = json.loads(text[start:end + 1])
                for item in (obj.get("herbs") or []):
                    nm = (item.get("name") if isinstance(item, dict) else str(item)).strip()
                    if nm:
                        names.append(nm)
                return names
        except Exception:
            pass
        # 兜底：按常见分隔粗提取
        for seg in text.replace("、", ",").replace("，", ",").replace("：", ":").split(","):
            seg = seg.strip()
            if 2 <= len(seg) <= 12 and not seg.startswith(("herbs", "note", "{")):
                names.append(seg)
        return names

    # ---------- 对外入口 ----------
    async def identify_image(self, image_bytes: bytes, source: str = "web") -> Dict:
        """
        识别单张图片：
        1) 调视觉模型拿药材名
        2) 归一化匹配库内药材
        3) 存识别记录
        返回结果（含匹配/未匹配列表）
        """
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        raw = await self._call_vision(image_b64)
        names = self._parse_herbs(raw)
        herbs_out = []
        primary = None
        for nm in names[:6]:
            m = self._match(nm)
            if m:
                herbs_out.append({**m, "source_name": nm, "matched": True})
                if primary is None:
                    primary = m
            else:
                herbs_out.append({"name": nm, "herb_id": None, "source_name": nm, "matched": False})

        # 落库：一条记录存主药（演示粒度），raw 保留完整
        record = RecognitionRecord(
            source=source,
            raw_text=raw[:2000],
            herb_name=primary["name"] if primary else (names[0] if names else None),
            herb_id=primary["herb_id"] if primary else None,
            matched=1 if primary else 0,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return {
            "id": record.id,
            "source": source,
            "raw": raw,
            "herbs": herbs_out,
            "matched_any": bool(primary),
            "primary": primary,
            "record_time": record.created_at.isoformat() if record.created_at else None,
            "vision_model": settings.VISION_MODEL,
        }
