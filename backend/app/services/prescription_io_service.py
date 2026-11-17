"""M01 方剂批量导入和导出。"""
import io
import json
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import xlrd
from openpyxl import Workbook, load_workbook
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ImportValidationError, ValidationError
from app.models.database_models import Herb, Prescription, PrescriptionHerb
from app.models.schemas import PrescriptionResponse, PrescriptionType


EXCEL_HEADERS = [
    "方剂名称",
    "拼音",
    "方剂类型",
    "来源",
    "功效",
    "主治",
    "用法",
    "禁忌",
    "分类",
    "组成药物",
]

TYPE_ALIASES = {
    "经典名方": "经典名方",
    "现代方剂": "现代方剂",
    "经验方": "经验方",
    "自定义方剂": "自定义方剂",
    "自拟方": "自定义方剂",
    "classic": "经典名方",
    "modern": "现代方剂",
    "experience": "经验方",
    "custom": "自定义方剂",
}


class PrescriptionIOService:
    """导入和导出方剂，所有行均独立提交。"""

    def __init__(self, db: Session):
        self.db = db

    async def import_file(
        self,
        filename: str,
        content: bytes,
        format_hint: str = "auto",
    ) -> dict:
        if len(content) > settings.MAX_IMPORT_FILE_SIZE:
            raise ImportValidationError(
                "导入文件不能超过10MB",
                {"max_size": settings.MAX_IMPORT_FILE_SIZE},
            )

        file_format = self._detect_format(filename, format_hint)
        if file_format == "json":
            rows = self._parse_json(content)
        else:
            rows = self._parse_excel(filename, content)

        if len(rows) > settings.MAX_IMPORT_ROWS:
            raise ImportValidationError(
                f"单次最多导入{settings.MAX_IMPORT_ROWS}行",
                {"max_rows": settings.MAX_IMPORT_ROWS, "actual": len(rows)},
            )

        known_names = {
            row[0].strip()
            for row in self.db.query(func.trim(Prescription.name)).all()
            if row[0]
        }
        result = {"total": len(rows), "created": 0, "skipped": 0, "failed": 0, "errors": []}

        for row_number, raw in rows:
            name = str(raw.get("name") or "").strip()
            try:
                if not name:
                    raise ValidationError("方剂名称不能为空")
                if name in known_names:
                    result["skipped"] += 1
                    continue

                self._create_row(raw, row_number)
                known_names.add(name)
                result["created"] += 1
            except Exception as exc:
                self.db.rollback()
                result["failed"] += 1
                result["errors"].append(
                    {
                        "row": row_number,
                        "name": name or None,
                        "code": getattr(exc, "code", "VALIDATION_ERROR"),
                        "message": getattr(exc, "message", str(exc)),
                    }
                )

        return result

    def export_json(self, prescriptions: Iterable[PrescriptionResponse]) -> bytes:
        payload = {"prescriptions": [self._export_item(item) for item in prescriptions]}
        return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

    def export_xlsx(self, prescriptions: Iterable[PrescriptionResponse]) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "方剂数据"
        sheet.append(EXCEL_HEADERS)
        for item in prescriptions:
            herb_text = "；".join(
                f"{herb.name}{herb.dosage or ''}" for herb in item.herbs
            )
            sheet.append(
                [
                    item.name,
                    item.pinyin or "",
                    item.type or "经典名方",
                    item.source or "",
                    item.functions or "",
                    item.indications or "",
                    item.usage or "",
                    item.precautions or "",
                    item.category or "",
                    herb_text,
                ]
            )
        output = io.BytesIO()
        workbook.save(output)
        return output.getvalue()

    # ==================== parsing ====================

    def _parse_json(self, content: bytes) -> List[Tuple[int, Dict[str, Any]]]:
        try:
            payload = json.loads(content.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ImportValidationError("JSON文件无法解析", {"reason": str(exc)}) from exc

        if isinstance(payload, dict):
            rows = payload.get("prescriptions")
            if not isinstance(rows, list):
                raise ImportValidationError("JSON对象必须包含 prescriptions 数组")
        elif isinstance(payload, list):
            rows = payload
        else:
            raise ImportValidationError("JSON顶层必须是数组或包含 prescriptions 的对象")

        parsed: List[Tuple[int, Dict[str, Any]]] = []
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise ImportValidationError(f"JSON第{index}条记录不是对象")
            parsed.append((index, row))
        return parsed

    def _parse_excel(self, filename: str, content: bytes) -> List[Tuple[int, Dict[str, Any]]]:
        lower = filename.lower()
        if lower.endswith(".xls"):
            return self._parse_xls(content)
        if not lower.endswith(".xlsx"):
            raise ImportValidationError("仅支持 .json、.xlsx 或 .xls 文件")
        try:
            workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        except Exception as exc:
            raise ImportValidationError("Excel文件无法解析", {"reason": str(exc)}) from exc

        sheet = workbook.worksheets[0]
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            raise ImportValidationError("Excel文件没有数据")
        headers = [str(value).strip() if value is not None else "" for value in rows[0]]
        if headers[: len(EXCEL_HEADERS)] != EXCEL_HEADERS:
            raise ImportValidationError(
                "Excel表头不符合模板定义",
                {"expected": EXCEL_HEADERS, "actual": headers},
            )

        parsed: List[Tuple[int, Dict[str, Any]]] = []
        for row_number, values in enumerate(rows[1:], start=2):
            if not any(value not in (None, "") for value in values):
                continue
            parsed.append((row_number, self._excel_values_to_row(values)))
        return parsed

    def _parse_xls(self, content: bytes) -> List[Tuple[int, Dict[str, Any]]]:
        try:
            workbook = xlrd.open_workbook(file_contents=content)
        except Exception as exc:
            raise ImportValidationError("Excel文件无法解析", {"reason": str(exc)}) from exc
        sheet = workbook.sheet_by_index(0)
        if sheet.nrows == 0:
            raise ImportValidationError("Excel文件没有数据")
        headers = [str(sheet.cell_value(0, col)).strip() for col in range(sheet.ncols)]
        if headers[: len(EXCEL_HEADERS)] != EXCEL_HEADERS:
            raise ImportValidationError(
                "Excel表头不符合模板定义",
                {"expected": EXCEL_HEADERS, "actual": headers},
            )

        parsed: List[Tuple[int, Dict[str, Any]]] = []
        for row_index in range(1, sheet.nrows):
            values = [sheet.cell_value(row_index, col) for col in range(sheet.ncols)]
            if not any(value not in (None, "") for value in values):
                continue
            parsed.append((row_index + 1, self._excel_values_to_row(values)))
        return parsed

    def _excel_values_to_row(self, values: Iterable[Any]) -> Dict[str, Any]:
        cells = list(values)
        row: Dict[str, Any] = {}
        for index, key in enumerate(
            [
                "name",
                "pinyin",
                "type",
                "source",
                "functions",
                "indications",
                "usage",
                "precautions",
                "category",
                "herb_text",
            ]
        ):
            value = cells[index] if index < len(cells) else None
            row[key] = "" if value is None else str(value).strip()
        return row

    # ==================== row import ====================

    def _create_row(self, raw: Dict[str, Any], row_number: int) -> None:
        name = str(raw.get("name") or "").strip()
        if not name:
            raise ValidationError("方剂名称不能为空")

        type_value = self._normalize_type(raw.get("type"))
        herbs = self._resolve_herbs(raw.get("herbs"), raw.get("herb_text"))
        if len(herbs) < 2:
            raise ValidationError("方剂至少包含2味药物")
        if len(herbs) > 30:
            raise ValidationError("方剂最多包含30味药物")

        now = datetime.now()
        prescription = Prescription(
            name=name,
            pinyin=self._text(raw.get("pinyin")),
            type=type_value,
            source=self._text(raw.get("source")),
            functions=self._text(raw.get("functions")),
            indications=self._text(raw.get("indications")),
            usage=self._text(raw.get("usage")),
            precautions=self._text(raw.get("precautions")),
            category=self._text(raw.get("category")),
            created_at=now,
            updated_at=now,
        )
        self.db.add(prescription)
        self.db.flush()
        for item in herbs:
            self.db.add(
                PrescriptionHerb(
                    prescription_id=prescription.id,
                    herb_id=item["herb_id"],
                    dosage=item["dosage"] or None,
                    preparation=item["preparation"] or None,
                    order=item["order"],
                )
            )
        self.db.commit()

    def _resolve_herbs(
        self,
        herbs: Any,
        herb_text: Any,
    ) -> List[Dict[str, Any]]:
        if isinstance(herbs, list):
            return [self._resolve_json_herb(item, index) for index, item in enumerate(herbs, start=1)]

        text = self._text(herb_text)
        if not text:
            raise ValidationError("组成药物不能为空")
        parts = [part.strip() for part in re.split(r"[；;，,]", text) if part.strip()]
        if not parts:
            raise ValidationError("组成药物不能为空")
        return [self._resolve_text_herb(part, index) for index, part in enumerate(parts, start=1)]

    def _resolve_json_herb(self, item: Any, index: int) -> Dict[str, Any]:
        if not isinstance(item, dict):
            raise ValidationError(f"第{index}味药物不是对象")
        herb_id = item.get("herb_id")
        if herb_id not in (None, ""):
            try:
                herb_id_int = int(herb_id)
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"第{index}味药物 herb_id 不合法") from exc
            herb = self.db.query(Herb).filter(Herb.id == herb_id_int).first()
            if not herb:
                raise ValidationError(f"药材ID {herb_id_int} 不存在")
        else:
            name = self._text(item.get("name"))
            if not name:
                raise ValidationError(f"第{index}味药物缺少 name 或 herb_id")
            herb = self.db.query(Herb).filter(func.trim(Herb.name) == name).first()
            if not herb:
                raise ValidationError(f"药材“{name}”不存在")

        return {
            "herb_id": herb.id,
            "dosage": self._text(item.get("dosage")) or "",
            "preparation": self._text(item.get("preparation")) or "",
            "order": item.get("order") or index,
        }

    def _resolve_text_herb(self, part: str, index: int) -> Dict[str, Any]:
        name, dosage = self._split_herb_text(part)
        herb = self.db.query(Herb).filter(func.trim(Herb.name) == name).first()
        if not herb:
            raise ValidationError(f"药材“{name}”不存在")
        return {
            "herb_id": herb.id,
            "dosage": dosage,
            "preparation": "",
            "order": index,
        }

    @staticmethod
    def _split_herb_text(text: str) -> Tuple[str, str]:
        value = text.strip()
        match = re.match(
            r"^(.+?)(\d+(?:\.\d+)?(?:\s*[~～\-]\s*\d+(?:\.\d+)?)?)([A-Za-z\u4e00-\u9fff]*)$",
            value,
        )
        if not match:
            return value, ""
        return match.group(1).strip(), f"{match.group(2)}{match.group(3)}".strip()

    # ==================== export helpers ====================

    @staticmethod
    def _export_item(item: PrescriptionResponse) -> Dict[str, Any]:
        return {
            "name": item.name,
            "pinyin": item.pinyin,
            "type": item.type,
            "source": item.source,
            "functions": item.functions,
            "indications": item.indications,
            "usage": item.usage,
            "precautions": item.precautions,
            "category": item.category,
            "herbs": [
                {
                    "herb_id": herb.herb_id,
                    "name": herb.name,
                    "dosage": herb.dosage,
                    "preparation": herb.preparation or "",
                    "order": herb.order,
                }
                for herb in item.herbs
            ],
        }

    @staticmethod
    def _normalize_type(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return PrescriptionType.CLASSIC.value
        if text not in TYPE_ALIASES:
            raise ValidationError(f"方剂类型“{text}”不合法")
        return TYPE_ALIASES[text]

    @staticmethod
    def _text(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _detect_format(filename: str, format_hint: str) -> str:
        hint = (format_hint or "auto").lower()
        if hint not in {"auto", "json", "excel"}:
            raise ImportValidationError("format 必须是 auto、json 或 excel")
        if hint != "auto":
            return hint
        lower = filename.lower()
        if lower.endswith(".json"):
            return "json"
        if lower.endswith(".xlsx") or lower.endswith(".xls"):
            return "excel"
        raise ImportValidationError("仅支持 .json、.xlsx 或 .xls 文件")
