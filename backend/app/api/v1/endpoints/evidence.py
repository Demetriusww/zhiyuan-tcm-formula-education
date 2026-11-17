"""M05 古籍证据检索 API。"""
import json
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import asc, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import DatabaseError, NotFoundError
from app.models.database_models import AncientBook
from app.models.schemas import APIResponse, AncientBookResponse

router = APIRouter(tags=["古籍文献"])


def _parse_prescriptions(value: Optional[str]) -> List[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()]


def _to_response(book: AncientBook) -> AncientBookResponse:
    return AncientBookResponse(
        id=book.id,
        title=book.title,
        dynasty=book.dynasty,
        author=book.author,
        category=book.category,
        description=book.description,
        content=book.content,
        prescriptions=_parse_prescriptions(book.prescriptions),
        source_url=book.source_url,
        sort_order=book.sort_order or 0,
    )


def _facets(db: Session) -> Dict[str, List[str]]:
    dynasties = [
        value
        for (value,) in db.query(AncientBook.dynasty)
        .filter(AncientBook.dynasty.isnot(None))
        .distinct()
        .order_by(asc(AncientBook.dynasty))
        .all()
        if value
    ]
    categories = [
        value
        for (value,) in db.query(AncientBook.category)
        .filter(AncientBook.category.isnot(None))
        .distinct()
        .order_by(asc(AncientBook.category))
        .all()
        if value
    ]
    return {"dynasties": dynasties, "categories": categories}


@router.get("/books", response_model=APIResponse, summary="检索古籍文献")
async def search_books(
    keyword: Optional[str] = Query(None, description="书名、作者、简介、内容或方剂关键词"),
    dynasty: Optional[str] = Query(None, description="朝代"),
    category: Optional[str] = Query(None, description="古籍分类"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(AncientBook)
        keyword_text = (keyword or "").strip()
        if keyword_text:
            pattern = f"%{keyword_text}%"
            query = query.filter(
                or_(
                    AncientBook.title.ilike(pattern),
                    AncientBook.author.ilike(pattern),
                    AncientBook.description.ilike(pattern),
                    AncientBook.content.ilike(pattern),
                    AncientBook.prescriptions.ilike(pattern),
                )
            )
        if dynasty:
            query = query.filter(AncientBook.dynasty == dynasty.strip())
        if category:
            query = query.filter(AncientBook.category == category.strip())

        total = query.count()
        rows = (
            query.order_by(asc(AncientBook.sort_order), asc(AncientBook.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        total_pages = (total + page_size - 1) // page_size if total else 0
        return APIResponse(
            message="检索成功",
            data={
                "items": [_to_response(row) for row in rows],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "facets": _facets(db),
            },
        )
    except Exception as exc:
        raise DatabaseError(f"古籍检索失败: {exc}") from exc


@router.get("/books/{book_id}", response_model=APIResponse, summary="获取古籍详情")
async def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(AncientBook).filter(AncientBook.id == book_id).first()
    if not book:
        raise NotFoundError(f"古籍ID {book_id} 不存在")
    return APIResponse(message="获取成功", data=_to_response(book))


@router.get("/books/{book_id}/download", summary="下载古籍文本")
async def download_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(AncientBook).filter(AncientBook.id == book_id).first()
    if not book:
        raise NotFoundError(f"古籍ID {book_id} 不存在")

    prescriptions = _parse_prescriptions(book.prescriptions)
    lines = [
        f"《{book.title}》",
        "",
        f"朝代：{book.dynasty or '未标注'}",
        f"作者：{book.author or '未标注'}",
        f"分类：{book.category or '未标注'}",
        f"来源：{book.source_url or '未标注'}",
        "",
        "简介",
        book.description or "未收录简介",
        "",
        "内容提要",
        book.content or "未收录内容提要",
    ]
    if prescriptions:
        lines.extend(["", "相关方剂", "、".join(prescriptions)])
    content = ("\n".join(lines) + "\n").encode("utf-8-sig")

    ascii_filename = f"ancient_book_{book.id}.txt"
    utf8_filename = quote(f"{book.title}.txt")
    return StreamingResponse(
        iter([content]),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_filename}"; '
                f"filename*=UTF-8''{utf8_filename}"
            )
        },
    )
