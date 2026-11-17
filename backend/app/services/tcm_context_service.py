"""Public-education context assembled from the bundled prescription data."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).resolve().parents[2] / "seed" / "prescriptions_all.json"
MAX_PRESCRIPTIONS = 4
MAX_HERBS = 6


@lru_cache(maxsize=1)
def _load_reference_data() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    prescriptions = payload.get("prescriptions", [])
    herbs = payload.get("herbs", {})
    return prescriptions, herbs


def _unique_names(rows: list[dict[str, Any]]) -> tuple[str, ...]:
    names: list[str] = []
    for row in rows:
        name = str(row.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
    return tuple(names)


def _format_prescription(row: dict[str, Any]) -> str:
    herb_names = "、".join(row.get("herb_names") or [])
    return (
        f"方剂：{row.get('name', '')}\n"
        f"- 出处线索：{row.get('source', '')}\n"
        f"- 类别：{row.get('category', '')}\n"
        f"- 传统功用：{row.get('functions', '')}\n"
        f"- 传统主治：{row.get('indications', '')}\n"
        f"- 资料组成：{row.get('herbs_raw', '')}\n"
        f"- 组成药名：{herb_names}"
    )


def _format_herb(row: dict[str, Any]) -> str:
    return (
        f"中药：{row.get('name', '')}\n"
        f"- 性味：{row.get('property', '')}\n"
        f"- 归经：{row.get('meridian', '')}\n"
        f"- 传统功能：{row.get('functions', '')}\n"
        f"- 传统主治：{row.get('indications', '')}\n"
        f"- 资料参考用量：{row.get('dosage', '')}\n"
        f"- 使用注意：{row.get('precautions', '')}"
    )


def build_local_context(question: str) -> str:
    """Return a compact, source-grounded context for names found in the text."""
    query = (question or "").strip()
    if not query:
        return ""

    prescriptions, herbs = _load_reference_data()
    matched_prescriptions = sorted(
        (
            row
            for row in prescriptions
            if str(row.get("name") or "") and str(row["name"]) in query
        ),
        key=lambda row: len(str(row["name"])),
        reverse=True,
    )

    matched_categories = {
        str(row.get("category") or "")
        for row in prescriptions
        if row.get("category") and str(row["category"]) in query
    }
    category_rows: list[dict[str, Any]] = []
    if not matched_prescriptions and matched_categories:
        for row in prescriptions:
            if row.get("category") in matched_categories:
                category_rows.append(row)
            if len(category_rows) >= MAX_PRESCRIPTIONS:
                break
        matched_prescriptions = category_rows

    matched_prescriptions = matched_prescriptions[:MAX_PRESCRIPTIONS]
    matched_herbs = sorted(
        (
            row
            for name, row in herbs.items()
            if name and name in query
        ),
        key=lambda row: len(str(row.get("name") or "")),
        reverse=True,
    )[:MAX_HERBS]

    sections: list[str] = [
        "以下是平台随附资料检索到的条目，仅作为本次科普回答的事实依据。"
        "资料没有覆盖的方源、组成、剂量或现代研究，不要自行补造。"
    ]
    sections.extend(_format_prescription(row) for row in matched_prescriptions)
    sections.extend(_format_herb(row) for row in matched_herbs)

    if len(sections) == 1:
        return ""
    return "\n\n".join(sections)


def matched_local_names(question: str) -> dict[str, tuple[str, ...]]:
    """Expose matched names for diagnostics and tests."""
    query = (question or "").strip()
    prescriptions, herbs = _load_reference_data()
    prescription_rows = [
        row for row in prescriptions if str(row.get("name") or "") in query
    ][:MAX_PRESCRIPTIONS]
    herb_rows = [
        row for name, row in herbs.items() if name in query
    ][:MAX_HERBS]
    return {
        "prescriptions": _unique_names(prescription_rows),
        "herbs": _unique_names(herb_rows),
    }
