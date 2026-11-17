"""M01 方剂数据管理 API 契约测试。"""
import io
import json

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.database_models import Herb, User


@pytest.fixture()
def api():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    with TestingSessionLocal() as db:
        db.add_all(
            [
                Herb(name="人参", pinyin="Ren Shen"),
                Herb(name="白术", pinyin="Bai Zhu"),
                Herb(name="茯苓", pinyin="Fu Ling"),
                Herb(name="甘草", pinyin="Gan Cao"),
                User(
                    username="tester",
                    password_hash="not-used-in-tests",
                    nickname="测试用户",
                    role="user",
                    is_active=True,
                ),
                User(
                    username="admin",
                    password_hash="not-used-in-tests",
                    nickname="管理员",
                    role="admin",
                    is_active=True,
                ),
            ]
        )
        db.commit()

    yield client, TestingSessionLocal

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _token(session_factory, username="tester"):
    with session_factory() as db:
        user = db.query(User).filter(User.username == username).one()
        return create_access_token(user.id, user.username)


def _auth_header(session_factory, username="tester"):
    return {"Authorization": f"Bearer {_token(session_factory, username)}"}


def _payload(name="四君子汤"):
    return {
        "name": name,
        "pinyin": "Si Jun Zi Tang",
        "type": "经典名方",
        "source": "太平惠民和剂局方",
        "functions": "益气健脾",
        "indications": "脾胃气虚证",
        "usage": "水煎服",
        "precautions": "阴虚火旺者慎用",
        "category": "补益剂",
        "herbs": [
            {"herb_id": 1, "name": "人参", "dosage": "9g", "order": 1},
            {"herb_id": 2, "name": "白术", "dosage": "9g", "order": 2},
            {"herb_id": 3, "name": "茯苓", "dosage": "9g", "order": 3},
        ],
    }


def test_m01_crud_permissions_and_error_envelope(api):
    client, sessions = api

    unauthorized = client.post("/api/v1/prescriptions", json=_payload())
    assert unauthorized.status_code == 401
    assert unauthorized.json()["code"] == "AUTHENTICATION_ERROR"
    assert unauthorized.json()["timestamp"]

    created = client.post(
        "/api/v1/prescriptions",
        json=_payload(),
        headers=_auth_header(sessions),
    )
    assert created.status_code == 201
    assert created.json()["code"] == "SUCCESS"
    prescription_id = created.json()["data"]["id"]
    assert created.json()["data"]["category"] == "补益剂"

    duplicate = client.post(
        "/api/v1/prescriptions",
        json=_payload("  四君子汤  "),
        headers=_auth_header(sessions),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "DUPLICATE_ERROR"

    updated = client.put(
        f"/api/v1/prescriptions/{prescription_id}",
        json={"type": "现代方剂", "category": "自定义分类"},
        headers=_auth_header(sessions),
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["type"] == "现代方剂"
    assert updated.json()["data"]["category"] == "自定义分类"

    public_detail = client.get(f"/api/v1/prescriptions/{prescription_id}")
    assert public_detail.status_code == 200
    assert public_detail.json()["data"]["name"] == "四君子汤"

    deleted = client.delete(
        f"/api/v1/prescriptions/{prescription_id}",
        headers=_auth_header(sessions),
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"] is None

    missing = client.get(f"/api/v1/prescriptions/{prescription_id}")
    assert missing.status_code == 404
    assert missing.json()["code"] == "NOT_FOUND"


def test_m01_search_filter_sort_and_pagination(api):
    client, sessions = api
    headers = _auth_header(sessions)
    for name, pinyin, functions in [
        ("补中益气汤", "Bu Zhong Yi Qi Tang", "补中益气"),
        ("四君子汤", "Si Jun Zi Tang", "益气健脾"),
        ("参苓白术散", "Shen Ling Bai Zhu San", "益气健脾渗湿"),
    ]:
        payload = _payload(name)
        payload["pinyin"] = pinyin
        payload["functions"] = functions
        assert client.post("/api/v1/prescriptions", json=payload, headers=headers).status_code == 201

    searched = client.get(
        "/api/v1/prescriptions",
        params={"keyword": "健脾", "page": 1, "page_size": 1, "sort_by": "name", "sort_order": "asc"},
    )
    assert searched.status_code == 200
    page = searched.json()["data"]
    assert page["total"] == 2
    assert page["total_pages"] == 2
    assert page["items"][0]["name"] == "参苓白术散"

    filtered = client.get(
        "/api/v1/prescriptions",
        params={"name": "四君", "type": "经典名方", "category": "补益剂"},
    )
    assert filtered.status_code == 200
    assert [item["name"] for item in filtered.json()["data"]["items"]] == ["四君子汤"]

    invalid_sort = client.get(
        "/api/v1/prescriptions",
        params={"sort_by": "unknown"},
    )
    assert invalid_sort.status_code == 422
    assert invalid_sort.json()["code"] == "VALIDATION_ERROR"


def test_m01_json_import_and_export_roundtrip(api):
    client, sessions = api
    headers = _auth_header(sessions)
    payload = {
        "prescriptions": [
            {
                "name": "四君子汤",
                "type": "经典名方",
                "category": "补益剂",
                "herbs": [
                    {"name": "人参", "dosage": "9g"},
                    {"name": "白术", "dosage": "9g"},
                ],
            },
            {
                "name": "四君子汤",
                "type": "经典名方",
                "herbs": [
                    {"name": "人参", "dosage": "9g"},
                    {"name": "白术", "dosage": "9g"},
                ],
            },
            {
                "name": "错误方",
                "herbs": [
                    {"name": "不存在", "dosage": "9g"},
                    {"name": "人参", "dosage": "9g"},
                ],
            },
        ]
    }
    response = client.post(
        "/api/v1/prescriptions/import",
        files={
            "file": (
                "prescriptions.json",
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                "application/json",
            )
        },
        headers=headers,
    )
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["total"] == 3
    assert result["created"] == 1
    assert result["skipped"] == 1
    assert result["failed"] == 1
    assert result["errors"][0]["row"] == 3

    exported = client.get("/api/v1/prescriptions/export", params={"format": "json"})
    assert exported.status_code == 200
    assert "attachment" in exported.headers["content-disposition"]
    exported_payload = json.loads(exported.content.decode("utf-8"))
    assert exported_payload["prescriptions"][0]["name"] == "四君子汤"

    reimport = client.post(
        "/api/v1/prescriptions/import",
        files={
            "file": (
                "roundtrip.json",
                exported.content,
                "application/json",
            )
        },
        headers=headers,
    )
    assert reimport.status_code == 200
    assert reimport.json()["data"]["skipped"] == 1


def test_m01_excel_export_can_be_imported_again(api):
    client, sessions = api
    headers = _auth_header(sessions)
    created = client.post("/api/v1/prescriptions", json=_payload(), headers=headers)
    assert created.status_code == 201

    exported = client.get("/api/v1/prescriptions/export", params={"format": "xlsx"})
    assert exported.status_code == 200
    workbook = load_workbook(io.BytesIO(exported.content), read_only=True)
    sheet = workbook.worksheets[0]
    assert [cell.value for cell in sheet[1]] == [
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

    reimport = client.post(
        "/api/v1/prescriptions/import",
        files={
            "file": (
                "roundtrip.xlsx",
                exported.content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=headers,
    )
    assert reimport.status_code == 200
    assert reimport.json()["data"]["skipped"] == 1


def test_m01_compare_route_is_reachable(api):
    client, sessions = api
    headers = _auth_header(sessions)
    first = client.post("/api/v1/prescriptions", json=_payload("方剂甲"), headers=headers)
    second_payload = _payload("方剂乙")
    second_payload["herbs"] = [
        {"herb_id": 1, "name": "人参", "dosage": "6g", "order": 1},
        {"herb_id": 4, "name": "甘草", "dosage": "3g", "order": 2},
    ]
    second = client.post("/api/v1/prescriptions", json=second_payload, headers=headers)

    response = client.post(
        "/api/v1/prescriptions/compare",
        json={
            "prescription_ids": [
                first.json()["data"]["id"],
                second.json()["data"]["id"],
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["code"] == "SUCCESS"
    assert len(response.json()["data"]["prescriptions"]) == 2
