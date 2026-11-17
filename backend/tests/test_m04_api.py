"""M04 药效预测 API 测试。"""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.exceptions import LLMServiceError
from app.core.security import get_current_user
from app.main import app
from app.models.database_models import (
    EfficacyPrediction as EfficacyPredictionModel,
    Herb,
    Prescription,
    PrescriptionHerb,
)
from app.models.schemas import EfficacyPrediction
from app.services.algorithm.compatibility_checker import checker
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


def _seed(session_factory):
    with session_factory() as db:
        herbs = {
            "人参": Herb(name="人参", functions="大补元气", indications="气虚"),
            "白术": Herb(name="白术", functions="健脾益气", indications="脾虚"),
            "茯苓": Herb(name="茯苓", functions="健脾渗湿", indications="脾虚湿盛"),
            "甘草": Herb(name="甘草", functions="调和诸药", indications="脾胃虚弱"),
            "附子": Herb(name="附子", functions="回阳救逆", indications="亡阳虚脱"),
            "半夏": Herb(name="半夏", functions="燥湿化痰", indications="痰湿"),
        }
        db.add_all(herbs.values())
        db.flush()

        normal = Prescription(
            name="四君子汤",
            type="经典名方",
            functions="益气健脾",
            indications="脾胃气虚证，食少便溏，倦怠乏力",
            source="太平惠民和剂局方",
        )
        conflict = Prescription(
            name="附子半夏示例方",
            type="经典名方",
            functions="温阳化痰",
            indications="阳虚痰阻",
        )
        sparse = Prescription(name="简方", type="自定义方剂")
        db.add_all([normal, conflict, sparse])
        db.flush()

        compositions = {
            normal.id: [("人参", "9g"), ("白术", "9g"), ("茯苓", "9g"), ("甘草", "6g")],
            conflict.id: [("附子", "9g"), ("半夏", "9g")],
            sparse.id: [("人参", "9g"), ("白术", "9g")],
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
        return normal.id, conflict.id, sparse.id


def _authenticate():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7)


def test_m04_requires_authentication():
    client, _, engine = _build_api()
    try:
        response = client.post(
            "/api/v1/efficacy/predict",
            json={
                "prescription_id": 1,
                "target_symptoms": ["乏力"],
            },
        )
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_ERROR"
    finally:
        _clear_api(engine)


def test_m04_success_uses_llm_and_persists(monkeypatch):
    client, session_factory, engine = _build_api()
    prescription_id, _, _ = _seed(session_factory)
    _authenticate()

    async def llm_result(*args, **kwargs):
        return EfficacyPrediction(
            prescription_id=0,
            target_symptoms=[],
            predicted_efficacy=88,
            confidence_level=0.86,
            mechanism_analysis="模型机制分析",
            supporting_evidence=["模型证据一", "模型证据二"],
            contraindications=[],
        )

    monkeypatch.setattr(llm_service, "predict_efficacy", llm_result)
    try:
        response = client.post(
            "/api/v1/efficacy/predict",
            json={
                "prescription_id": prescription_id,
                "target_symptoms": ["乏力", "食欲不振"],
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == "SUCCESS"
        result = body["data"]
        assert result["prediction_id"] > 0
        assert result["prescription_id"] == prescription_id
        assert result["target_symptoms"] == ["乏力", "食欲不振"]
        assert result["predicted_efficacy"] == 88
        assert result["confidence_level"] == 0.86
        assert result["mechanism_analysis"] == "模型机制分析"
        assert result["supporting_evidence"] == ["模型证据一", "模型证据二"]
        assert result["risk_level"] == "low"
        assert result["degraded"] is False
        assert result["created_at"]

        with session_factory() as db:
            record = db.query(EfficacyPredictionModel).one()
            assert record.user_id == 7
            assert record.prescription_id == prescription_id
            assert "乏力" in record.target_symptoms
    finally:
        _clear_api(engine)


def test_m04_llm_failure_falls_back_and_marks_conflict_risk(monkeypatch):
    client, session_factory, engine = _build_api()
    _, conflict_id, _ = _seed(session_factory)
    _authenticate()

    async def unavailable(*args, **kwargs):
        raise LLMServiceError("模型不可用")

    monkeypatch.setattr(llm_service, "predict_efficacy", unavailable)
    try:
        response = client.post(
            "/api/v1/efficacy/predict",
            json={
                "prescription_id": conflict_id,
                "target_symptoms": ["痰多"],
            },
        )
        assert response.status_code == 200, response.text
        result = response.json()["data"]
        assert result["degraded"] is True
        assert result["risk_level"] == "high"
        assert result["contraindications"]
        assert "十八反" in "".join(result["contraindications"])
        assert result["mechanism_analysis"]
        assert result["supporting_evidence"]
    finally:
        _clear_api(engine)


def test_m04_fallback_returns_medium_and_low_risk(monkeypatch):
    client, session_factory, engine = _build_api()
    normal_id, _, sparse_id = _seed(session_factory)
    _authenticate()

    async def unavailable(*args, **kwargs):
        raise LLMServiceError("模型不可用")

    monkeypatch.setattr(llm_service, "predict_efficacy", unavailable)
    try:
        low = client.post(
            "/api/v1/efficacy/predict",
            json={
                "prescription_id": normal_id,
                "target_symptoms": ["乏力"],
            },
        )
        assert low.status_code == 200, low.text
        assert low.json()["data"]["risk_level"] == "low"

        medium = client.post(
            "/api/v1/efficacy/predict",
            json={
                "prescription_id": sparse_id,
                "target_symptoms": ["未知症状"],
            },
        )
        assert medium.status_code == 200, medium.text
        assert medium.json()["data"]["risk_level"] == "medium"
    finally:
        _clear_api(engine)


def test_m04_not_found_and_delete_cleans_predictions(monkeypatch):
    client, session_factory, engine = _build_api()
    prescription_id, _, _ = _seed(session_factory)
    _authenticate()

    async def llm_result(*args, **kwargs):
        return EfficacyPrediction(
            prescription_id=0,
            target_symptoms=[],
            predicted_efficacy=80,
            confidence_level=0.8,
            mechanism_analysis="可测试机制",
            supporting_evidence=[],
            contraindications=[],
        )

    monkeypatch.setattr(llm_service, "predict_efficacy", llm_result)
    try:
        missing = client.post(
            "/api/v1/efficacy/predict",
            json={
                "prescription_id": 9999,
                "target_symptoms": ["乏力"],
            },
        )
        assert missing.status_code == 404
        assert missing.json()["code"] == "NOT_FOUND"

        predicted = client.post(
            "/api/v1/efficacy/predict",
            json={
                "prescription_id": prescription_id,
                "target_symptoms": ["乏力"],
            },
        )
        assert predicted.status_code == 200, predicted.text
        with session_factory() as db:
            assert db.query(EfficacyPredictionModel).count() == 1

        deleted = client.delete(f"/api/v1/prescriptions/{prescription_id}")
        assert deleted.status_code == 200, deleted.text
        with session_factory() as db:
            assert db.query(EfficacyPredictionModel).count() == 0
    finally:
        _clear_api(engine)


def test_m04_risk_level_rules_cover_medium():
    assert (
        __import__(
            "app.services.efficacy_service",
            fromlist=["EfficacyService"],
        ).EfficacyService._risk_level(
            ["人参"],
            60,
            0.7,
            ["禁忌一", "禁忌二"],
        )
        == "medium"
    )
    assert checker.check(["附子", "半夏"])
