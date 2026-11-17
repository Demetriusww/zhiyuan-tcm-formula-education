"""M05 古籍证据检索与聊天持久化 API 测试。"""
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.database_models import AncientBook, Conversation
from app.services.llm_service import llm_service


def _build_api():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), session_factory, engine


def _clear_api(engine):
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _seed_books(session_factory):
    with session_factory() as db:
        db.add_all(
            [
                AncientBook(
                    title="伤寒论",
                    dynasty="东汉",
                    author="张仲景",
                    category="医经",
                    description="创立六经辨证体系。",
                    content="论述外感热病的辨证论治。",
                    prescriptions=json.dumps(["桂枝汤", "麻黄汤"], ensure_ascii=False),
                    source_url="https://example.test/shanghan",
                    sort_order=1,
                ),
                AncientBook(
                    title="本草纲目",
                    dynasty="明",
                    author="李时珍",
                    category="本草",
                    description="中国古代药物学巨著。",
                    content="集十六世纪以前本草学之大成。",
                    prescriptions="[]",
                    source_url="https://example.test/bencao",
                    sort_order=2,
                ),
                AncientBook(
                    title="温病条辨",
                    dynasty="清",
                    author="吴鞠通",
                    category="温病",
                    description="温病学代表作。",
                    content="创立三焦辨证体系。",
                    prescriptions=json.dumps(["银翘散"], ensure_ascii=False),
                    source_url="https://example.test/wenbing",
                    sort_order=3,
                ),
            ]
        )
        db.commit()


def test_m05_search_filters_pagination_and_detail():
    client, session_factory, engine = _build_api()
    _seed_books(session_factory)
    try:
        response = client.get(
            "/api/v1/evidence/books",
            params={"keyword": "伤寒", "page": 1, "page_size": 1},
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 1
        assert data["total_pages"] == 1
        assert data["items"][0]["title"] == "伤寒论"
        assert data["items"][0]["prescriptions"] == ["桂枝汤", "麻黄汤"]
        assert set(data["facets"]["dynasties"]) == {"东汉", "明", "清"}
        assert set(data["facets"]["categories"]) == {"医经", "本草", "温病"}

        filtered = client.get(
            "/api/v1/evidence/books",
            params={"dynasty": "清", "category": "温病"},
        )
        assert filtered.status_code == 200, filtered.text
        filtered_data = filtered.json()["data"]
        assert filtered_data["total"] == 1
        assert filtered_data["items"][0]["title"] == "温病条辨"

        book_id = data["items"][0]["id"]
        detail = client.get(f"/api/v1/evidence/books/{book_id}")
        assert detail.status_code == 200, detail.text
        assert detail.json()["data"]["author"] == "张仲景"

        missing = client.get("/api/v1/evidence/books/99999")
        assert missing.status_code == 404
        assert missing.json()["code"] == "NOT_FOUND"
    finally:
        _clear_api(engine)


def test_m05_download_returns_real_utf8_text_attachment():
    client, session_factory, engine = _build_api()
    _seed_books(session_factory)
    try:
        book_id = client.get(
            "/api/v1/evidence/books",
            params={"keyword": "本草纲目"},
        ).json()["data"]["items"][0]["id"]
        response = client.get(f"/api/v1/evidence/books/{book_id}/download")
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("text/plain")
        assert "attachment" in response.headers["content-disposition"]
        text = response.content.decode("utf-8-sig")
        assert "《本草纲目》" in text
        assert "作者：李时珍" in text
        assert "内容提要" in text
    finally:
        _clear_api(engine)


def test_m05_chat_persists_reads_and_clears_history(monkeypatch):
    client, session_factory, engine = _build_api()

    async def fake_llm(*args, **kwargs):
        return "综合分析结果\n\n- **建议**：辨证使用"

    monkeypatch.setattr(llm_service, "_call_llm", fake_llm)
    try:
        response = client.post(
            "/api/v1/chat/analyze",
            json={
                "message": "请分析四君子汤",
                "sessionId": "test-session",
                "history": [],
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == "SUCCESS"
        assert body["data"]["sessionId"] == "test-session"
        assert "综合分析结果" in body["data"]["response"]
        assert body["data"]["persisted"] is True

        with session_factory() as db:
            rows = (
                db.query(Conversation)
                .filter(Conversation.session_id == "test-session")
                .order_by(Conversation.id)
                .all()
            )
            assert [(row.role, row.content) for row in rows] == [
                ("user", "请分析四君子汤"),
                ("assistant", "综合分析结果\n\n- **建议**：辨证使用"),
            ]

        history = client.get("/api/v1/chat/history/test-session")
        assert history.status_code == 200, history.text
        messages = history.json()["data"]["messages"]
        assert [item["role"] for item in messages] == ["user", "assistant"]
        assert messages[0]["created_at"]

        deleted = client.delete("/api/v1/chat/history/test-session")
        assert deleted.status_code == 200, deleted.text
        assert deleted.json()["data"]["deleted"] == 2

        empty = client.get("/api/v1/chat/history/test-session")
        assert empty.status_code == 200, empty.text
        assert empty.json()["data"]["messages"] == []
    finally:
        _clear_api(engine)
