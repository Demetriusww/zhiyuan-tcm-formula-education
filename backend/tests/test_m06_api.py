"""M06 管理员接口与认证契约测试。"""
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_current_user, hash_password
from app.main import app
from app.models.database_models import AuditLog, User


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


def _seed_users(session_factory):
    with session_factory() as db:
        admin = User(
            username="admin",
            password_hash=hash_password("secret123"),
            nickname="管理员",
            email="admin@example.com",
            role="admin",
            is_active=True,
        )
        user = User(
            username="user1",
            password_hash=hash_password("secret123"),
            nickname="用户一",
            email="user1@example.com",
            role="user",
            is_active=True,
        )
        disabled = User(
            username="disabled1",
            password_hash=hash_password("secret123"),
            nickname="停用用户",
            email="disabled@example.com",
            role="user",
            is_active=False,
        )
        db.add_all([admin, user, disabled])
        db.commit()
        return admin.id, user.id, disabled.id


def _set_current_user(user_id: int, username: str, role: str):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=user_id,
        username=username,
        role=role,
    )


def test_m06_auth_endpoints_use_standard_response_and_reject_disabled():
    client, session_factory, engine = _build_api()
    _seed_users(session_factory)
    try:
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "secret123"},
        )
        assert login.status_code == 200, login.text
        assert login.json()["code"] == "SUCCESS"
        assert login.json()["data"]["token"]
        assert login.json()["data"]["user"]["role"] == "admin"

        disabled = client.post(
            "/api/v1/auth/login",
            json={"username": "disabled1", "password": "secret123"},
        )
        assert disabled.status_code == 401
        assert disabled.json()["code"] == "AUTHENTICATION_ERROR"
        assert disabled.json()["message"] == "用户已被禁用"

        duplicate = client.post(
            "/api/v1/auth/register",
            json={"username": "admin", "password": "secret123"},
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "DUPLICATE_ERROR"
    finally:
        _clear_api(engine)


def test_m06_user_list_and_detail_require_admin():
    client, session_factory, engine = _build_api()
    admin_id, user_id, _ = _seed_users(session_factory)
    try:
        _set_current_user(admin_id, "admin", "admin")
        listing = client.get(
            "/api/v1/admin/users",
            params={"page": 1, "page_size": 10, "role": "user"},
        )
        assert listing.status_code == 200, listing.text
        body = listing.json()
        assert body["code"] == "SUCCESS"
        assert body["data"]["total"] == 2
        assert all("password_hash" not in item for item in body["data"]["items"])

        detail = client.get(f"/api/v1/admin/users/{user_id}")
        assert detail.status_code == 200, detail.text
        assert detail.json()["data"]["username"] == "user1"

        missing = client.get("/api/v1/admin/users/9999")
        assert missing.status_code == 404
        assert missing.json()["code"] == "NOT_FOUND"

        app.dependency_overrides.pop(get_current_user, None)
        _set_current_user(user_id, "user1", "user")
        forbidden = client.get("/api/v1/admin/users")
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "AUTHORIZATION_ERROR"
    finally:
        _clear_api(engine)


def test_m06_role_status_updates_are_audited():
    client, session_factory, engine = _build_api()
    admin_id, user_id, disabled_id = _seed_users(session_factory)
    _set_current_user(admin_id, "admin", "admin")
    try:
        role = client.put(
            f"/api/v1/admin/users/{user_id}/role",
            json={"role": "admin"},
        )
        assert role.status_code == 200, role.text
        assert role.json()["data"]["role"] == "admin"

        status = client.put(
            f"/api/v1/admin/users/{user_id}/status",
            json={"is_active": False},
        )
        assert status.status_code == 200, status.text
        assert status.json()["data"]["is_active"] is False

        enable = client.put(
            f"/api/v1/admin/users/{disabled_id}/status",
            json={"is_active": True},
        )
        assert enable.status_code == 200, enable.text
        assert enable.json()["data"]["is_active"] is True

        logs = client.get("/api/v1/admin/audit-logs?page=1&page_size=20")
        assert logs.status_code == 200, logs.text
        actions = [item["action"] for item in logs.json()["data"]["items"]]
        assert "change_role" in actions
        assert "disable_user" in actions
        assert "enable_user" in actions
        assert all(item["operator_name"] == "admin" for item in logs.json()["data"]["items"])

        with session_factory() as db:
            assert db.query(AuditLog).count() == 3
    finally:
        _clear_api(engine)


def test_m06_protects_current_admin_and_validates_payload():
    client, session_factory, engine = _build_api()
    admin_id, _, _ = _seed_users(session_factory)
    _set_current_user(admin_id, "admin", "admin")
    try:
        demote = client.put(
            f"/api/v1/admin/users/{admin_id}/role",
            json={"role": "user"},
        )
        assert demote.status_code == 422
        assert demote.json()["code"] == "VALIDATION_ERROR"

        disable = client.put(
            f"/api/v1/admin/users/{admin_id}/status",
            json={"is_active": False},
        )
        assert disable.status_code == 422
        assert disable.json()["code"] == "VALIDATION_ERROR"

        invalid_role = client.put(
            f"/api/v1/admin/users/{admin_id}/role",
            json={"role": "superuser"},
        )
        assert invalid_role.status_code == 422
        assert invalid_role.json()["code"] == "VALIDATION_ERROR"
    finally:
        _clear_api(engine)
