"""
种子数据灌库模块
启动时自动把方剂基础数据与古籍文献写入数据库。
"""
import json
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.migrations import ensure_database_schema
from app.core.logger import db_logger
from app.models.database_models import AncientBook, Herb, Prescription, PrescriptionHerb

SEED_FILE = Path(__file__).resolve().parent.parent.parent / "seed" / "prescriptions_all.json"
PRESCRIPTION_PINYIN_FILE = (
    Path(__file__).resolve().parent.parent.parent / "seed" / "prescription_pinyin.json"
)
ANCIENT_BOOKS_FILE = (
    Path(__file__).resolve().parent.parent.parent / "seed" / "ancient_books.json"
)


def _load_prescription_pinyin() -> dict:
    if not PRESCRIPTION_PINYIN_FILE.exists():
        return {}
    return json.loads(PRESCRIPTION_PINYIN_FILE.read_text(encoding="utf-8"))


def _parse_dosage(text: str):
    """从 '人参9g' 提取 (药名, 剂量)。剂量可能为 '9g'、'4枚'、'3片' 等"""
    m = re.match(r"^(.+?)([\d.]+(?:～|~|－|-)?[\d.]*)(g|克|枚|片|钱|两|个|升|分|粒|条|块|匙)?$", text.strip())
    if m:
        name = m.group(1).strip()
        amount = m.group(2)
        unit = m.group(3) or ""
        return name, f"{amount}{unit}"
    return text.strip(), ""


def seed_db(db: Session = None) -> dict:
    """灌入种子数据，各数据集独立判断，重复执行只补充缺失项。"""
    own_session = db is None
    if own_session:
        db = SessionLocal()

    result = {
        "herbs": 0,
        "prescriptions": 0,
        "links": 0,
        "ancient_books": 0,
        "skipped": False,
        "core_skipped": False,
        "evidence_skipped": False,
    }
    try:
        if not SEED_FILE.exists():
            db_logger.warning(f"种子数据文件不存在: {SEED_FILE}")
            result["core_skipped"] = True
        elif db.query(Herb).count() > 0:
            result["core_skipped"] = True
            db_logger.info("数据库已有方剂基础数据，跳过方剂种子灌入")
        else:
            core_result = _seed_core_data(db)
            result.update(core_result)

        if not ANCIENT_BOOKS_FILE.exists():
            db_logger.warning(f"古籍种子数据文件不存在: {ANCIENT_BOOKS_FILE}")
            result["evidence_skipped"] = True
        else:
            ancient_books_created = _seed_ancient_books(db)
            result["ancient_books"] = ancient_books_created
            result["evidence_skipped"] = ancient_books_created == 0

        result["skipped"] = result["core_skipped"] and result["evidence_skipped"]
        db_logger.info(
            "种子数据检查完成: 新增药材%s味 / 方剂%s个 / 关联%s条 / 古籍%s本",
            result["herbs"],
            result["prescriptions"],
            result["links"],
            result["ancient_books"],
        )
        return result

    except Exception as e:
        db.rollback()
        db_logger.error(f"种子数据灌入失败: {e}")
        raise
    finally:
        if own_session:
            db.close()


def _seed_core_data(db: Session) -> dict:
    """灌入药材、方剂和方剂药味关联。"""
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    herbs_json = data.get("herbs", {})
    prescriptions_json = data.get("prescriptions", [])
    prescription_pinyin = _load_prescription_pinyin()

    herb_id_map = {}
    for name, info in herbs_json.items():
        herb = Herb(
            name=name,
            pinyin=info.get("pinyin"),
            property=info.get("property"),
            flavor=info.get("flavor"),
            meridians=info.get("meridian") or info.get("meridians"),
            latin=info.get("latin"),
            functions=info.get("functions"),
            indications=info.get("indications"),
            dosage=info.get("dosage"),
            precautions=info.get("precautions"),
            modern_research=info.get("modernResearch"),
            description=info.get("description"),
            category=info.get("category"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(herb)
        db.flush()
        herb_id_map[name] = herb.id

    link_count = 0
    for p in prescriptions_json:
        presc = Prescription(
            name=p["name"],
            pinyin=p.get("pinyin") or prescription_pinyin.get(p["name"]),
            source=p.get("source"),
            functions=p.get("functions"),
            indications=p.get("indications"),
            category=p.get("category"),
            type="经典名方",
            description=p.get("description"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(presc)
        db.flush()

        raw_parts = [
            s
            for s in re.split(r"[、，,;；]", p.get("herbs_raw", ""))
            if s.strip()
        ]
        parsed = [_parse_dosage(part) for part in raw_parts]
        if len(parsed) == len(p["herb_names"]):
            pairs = list(zip(p["herb_names"], [d for _, d in parsed]))
        else:
            pairs = [(n, "") for n in p["herb_names"]]

        for order, (herb_name, dosage) in enumerate(pairs, start=1):
            herb_id = herb_id_map.get(herb_name)
            if herb_id is None:
                db_logger.warning(
                    "方剂 %s 引用了未收录药材: %s，已跳过该关联",
                    p["name"],
                    herb_name,
                )
                continue
            db.add(
                PrescriptionHerb(
                    prescription_id=presc.id,
                    herb_id=herb_id,
                    dosage=dosage or None,
                    order=order,
                )
            )
            link_count += 1

    db.commit()
    return {
        "herbs": len(herb_id_map),
        "prescriptions": len(prescriptions_json),
        "links": link_count,
    }


def _seed_ancient_books(db: Session) -> int:
    """按书名补齐古籍记录，已存在的书名直接跳过。"""
    payload = json.loads(ANCIENT_BOOKS_FILE.read_text(encoding="utf-8"))
    books = payload.get("books", [])
    existing_titles = {
        (title or "").strip()
        for (title,) in db.query(AncientBook.title).all()
    }
    created = 0
    for item in books:
        title = str(item.get("title", "")).strip()
        if not title or title in existing_titles:
            continue
        prescriptions = item.get("prescriptions") or []
        if not isinstance(prescriptions, list):
            prescriptions = []
        db.add(
            AncientBook(
                title=title,
                dynasty=item.get("dynasty"),
                author=item.get("author"),
                category=item.get("category"),
                description=item.get("description"),
                content=item.get("content"),
                prescriptions=json.dumps(prescriptions, ensure_ascii=False),
                source_url=item.get("source_url"),
                sort_order=int(item.get("sort_order") or 0),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )
        existing_titles.add(title)
        created += 1
    db.commit()
    return created


def init_and_seed():
    """执行迁移并灌入种子数据(供启动时调用)"""
    ensure_database_schema()
    return seed_db()
