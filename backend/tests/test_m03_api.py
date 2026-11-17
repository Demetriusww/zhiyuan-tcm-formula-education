"""M03 配伍分析、方剂优化和多维对比 API 测试。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.exceptions import LLMServiceError
from app.main import app
from app.models.database_models import Herb
from app.services.llm_service import llm_service


@pytest.fixture()
def api():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    with session_factory() as db:
        db.add_all(
            [
                Herb(name="人参", property="甘、微苦，平", meridians="归脾、肺、心经"),
                Herb(name="白术", property="甘、苦，温", meridians="归脾、胃经"),
                Herb(name="茯苓", property="甘、淡，平", meridians="归心、肺、脾、肾经"),
                Herb(name="甘草", property="甘，平", meridians="归心、肺、脾、胃经"),
                Herb(name="附子", property="辛、甘，大热；有毒", meridians="归心、肾、脾经"),
                Herb(name="半夏", property="辛，温；有毒", meridians="归脾、胃、肺经"),
            ]
        )
        db.commit()

    yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _create_prescription(
    client: TestClient,
    name: str,
    herb_ids: list[tuple[int, str, str]],
) -> dict:
    response = client.post(
        "/api/v1/prescriptions",
        json={
            "name": name,
            "type": "经典名方",
            "functions": "益气健脾",
            "indications": "脾胃气虚证",
            "herbs": [
                {
                    "herb_id": herb_id,
                    "name": herb_name,
                    "dosage": dosage,
                    "order": index,
                }
                for index, (herb_id, herb_name, dosage) in enumerate(herb_ids, start=1)
            ],
        },
        headers={"Authorization": "Bearer invalid-for-write-test"},
    )
    return response


def _seed_prescriptions(client: TestClient) -> tuple[dict, dict]:
    # 创建接口按契约要求登录；M03 测试临时跳过鉴权，避免复制认证夹具。
    from app.core.security import get_current_user

    app.dependency_overrides[get_current_user] = lambda: object()
    first = _create_prescription(
        client,
        "四君子汤",
        [
            (1, "人参", "9g"),
            (2, "白术", "9g"),
            (3, "茯苓", "9g"),
            (4, "甘草", "6g"),
        ],
    )
    second = _create_prescription(
        client,
        "附子半夏示例方",
        [
            (5, "附子", "9g"),
            (6, "半夏", "9g"),
            (1, "人参", "6g"),
            (4, "甘草", "3g"),
        ],
    )
    app.dependency_overrides.pop(get_current_user, None)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    return first.json()["data"], second.json()["data"]


def test_m03_analysis_conflict_and_llm_fallback(api, monkeypatch):
    client = api
    _, conflict_prescription = _seed_prescriptions(client)

    async def unavailable(*args, **kwargs):
        raise LLMServiceError("模型不可用")

    monkeypatch.setattr(llm_service, "analyze_compatibility", unavailable)
    response = client.post(
        f"/api/v1/prescriptions/{conflict_prescription['id']}/analyze"
    )
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["degraded"] is True
    assert result["overall_score"] < 80
    assert result["potential_conflicts"]
    assert "十八反" in result["potential_conflicts"][0]
    assert result["monarch_herb"]["name"] == "附子"


def test_m03_optimization_returns_real_change_and_fallback(api, monkeypatch):
    client = api
    _, prescription = _seed_prescriptions(client)

    async def unavailable(*args, **kwargs):
        raise LLMServiceError("模型不可用")

    monkeypatch.setattr(
        llm_service,
        "generate_optimization_suggestions",
        unavailable,
    )
    response = client.post(
        f"/api/v1/prescriptions/{prescription['id']}/optimize",
        json={"target_symptoms": ["乏力", "食欲不振"]},
    )
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["degraded"] is True
    assert result["changes"]
    assert result["suggestions"]
    assert result["risk_assessment"]
    assert result["original_prescription"]["herbs"] != result["optimized_prescription"]["herbs"]


def test_m03_comparison_has_dimension_scores(api, monkeypatch):
    client = api
    first, second = _seed_prescriptions(client)
    response = client.post(
        "/api/v1/prescriptions/compare",
        json={"prescription_ids": [first["id"], second["id"]]},
    )
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["comparison_dimensions"] == [
        "功效",
        "安全性",
        "药味数量",
        "剂量合理性",
        "配伍协调",
    ]
    assert set(result["dimension_scores"]) == {str(first["id"]), str(second["id"])}
    assert all(
        set(result["dimension_scores"][str(item["id"])])
        == set(result["comparison_dimensions"])
        for item in result["prescriptions"]
    )
    assert "综合评分最高" in result["recommendation"]


def test_m03_validation_and_not_found(api):
    client = api
    insufficient = client.post(
        "/api/v1/prescriptions/compare",
        json={"prescription_ids": [1]},
    )
    assert insufficient.status_code == 422
    assert insufficient.json()["code"] == "VALIDATION_ERROR"

    missing = client.post("/api/v1/prescriptions/999/analyze")
    assert missing.status_code == 404
    assert missing.json()["code"] == "NOT_FOUND"
