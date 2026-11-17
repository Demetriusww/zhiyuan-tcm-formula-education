"""M02 标准智能方剂推荐 API 测试。"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.exceptions import LLMServiceError
from app.main import app
from app.models.database_models import Herb, Prescription, PrescriptionHerb
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


def _seed_prescriptions(session_factory):
    with session_factory() as db:
        herbs = {
            "人参": Herb(name="人参", functions="大补元气", indications="气虚"),
            "白术": Herb(name="白术", functions="健脾益气", indications="脾虚"),
            "茯苓": Herb(name="茯苓", functions="健脾渗湿", indications="脾虚湿盛"),
            "甘草": Herb(name="甘草", functions="调和诸药", indications="脾胃虚弱"),
            "黄芪": Herb(name="黄芪", functions="补气升阳", indications="中气下陷"),
            "当归": Herb(name="当归", functions="补血活血", indications="血虚"),
        }
        db.add_all(herbs.values())
        db.flush()

        first = Prescription(
            name="四君子汤",
            type="经典名方",
            source="太平惠民和剂局方",
            functions="益气健脾",
            indications="脾胃气虚证，食少便溏，倦怠乏力",
            category="补益剂",
        )
        second = Prescription(
            name="补中益气汤",
            type="经典名方",
            source="脾胃论",
            functions="补中益气，升阳举陷",
            indications="脾胃气虚，少气懒言，体倦肢软",
            category="补益剂",
        )
        db.add_all([first, second])
        db.flush()

        compositions = {
            first.id: [("人参", "9g"), ("白术", "9g"), ("茯苓", "9g"), ("甘草", "6g")],
            second.id: [
                ("黄芪", "18g"),
                ("人参", "9g"),
                ("白术", "9g"),
                ("当归", "6g"),
                ("甘草", "6g"),
            ],
        }
        for prescription_id, rows in compositions.items():
            for index, (herb_name, dosage) in enumerate(rows, start=1):
                db.add(
                    PrescriptionHerb(
                        prescription_id=prescription_id,
                        herb_id=herbs[herb_name].id,
                        dosage=dosage,
                        order=index,
                    )
                )
        db.commit()


def test_m02_recommendations_are_ranked_and_traceable(monkeypatch):
    client, session_factory, engine = _build_api()
    _seed_prescriptions(session_factory)

    async def unavailable(*args, **kwargs):
        raise LLMServiceError("模型不可用")

    monkeypatch.setattr(llm_service, "recommend_prescriptions", unavailable)
    try:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "symptoms": "脾胃气虚，食少便溏，倦怠乏力",
                "constraints": {},
                "use_llm": True,
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == "SUCCESS"
        result = body["data"]
        assert result["degraded"] is True
        assert result["recommendations"]

        scores = [item["match_score"] for item in result["recommendations"]]
        assert scores == sorted(scores, reverse=True)
        first = result["recommendations"][0]
        assert first["prescription_id"] is not None
        assert first["name"]
        assert first["reasons"]
        assert first["core_herbs"]
        assert first["constraints_checked"] is True
        assert first["source"] == "database"
        assert "functions" in first
        assert "indications" in first
        assert "source_text" in first
        assert "conflict_warnings" in first
    finally:
        _clear_api(engine)


def test_m02_constraints_and_empty_result(monkeypatch):
    client, session_factory, engine = _build_api()
    _seed_prescriptions(session_factory)

    async def unavailable(*args, **kwargs):
        raise LLMServiceError("模型不可用")

    monkeypatch.setattr(llm_service, "recommend_prescriptions", unavailable)
    try:
        constrained = client.post(
            "/api/v1/recommendations",
            json={
                "symptoms": "脾胃气虚，食少便溏，倦怠乏力",
                "constraints": {
                    "avoid_herbs": ["人参"],
                    "max_herb_count": 4,
                },
                "use_llm": True,
            },
        )
        assert constrained.status_code == 200, constrained.text
        constrained_result = constrained.json()["data"]
        assert constrained_result["recommendations"] == []
        assert "约束" in constrained_result["reason"]

        empty = client.post(
            "/api/v1/recommendations",
            json={
                "symptoms": "量子纠缠现象",
                "constraints": {},
                "use_llm": False,
            },
        )
        assert empty.status_code == 200, empty.text
        empty_result = empty.json()["data"]
        assert empty_result["recommendations"] == []
        assert empty_result["reason"]
        assert empty_result["degraded"] is True
    finally:
        _clear_api(engine)


def test_m02_llm_result_is_merged_with_database(monkeypatch):
    client, session_factory, engine = _build_api()
    _seed_prescriptions(session_factory)

    async def llm_result(*args, **kwargs):
        return [
            {
                "name": "四君子汤",
                "match_score": 98,
                "reason": "模型判断与脾胃气虚证高度匹配",
                "herbs": ["人参", "白术", "茯苓", "甘草"],
            }
        ]

    monkeypatch.setattr(llm_service, "recommend_prescriptions", llm_result)
    try:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "symptoms": "脾胃气虚，食少便溏，倦怠乏力",
                "constraints": {},
                "use_llm": True,
            },
        )
        assert response.status_code == 200, response.text
        result = response.json()["data"]
        first = result["recommendations"][0]
        assert first["name"] == "四君子汤"
        assert first["match_score"] >= 98
        assert first["source"] == "database+llm"
        assert first["degraded"] is False
        assert "模型判断与脾胃气虚证高度匹配" in first["reasons"]
    finally:
        _clear_api(engine)


def test_m02_request_validation():
    client, session_factory, engine = _build_api()
    try:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "symptoms": "短",
                "constraints": {"max_herb_count": 1},
                "use_llm": False,
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert body["message"] == "请求参数不合法"
    finally:
        _clear_api(engine)
