import pytest
from app.core.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.models.user import User, UserRole, UserStatus


class TestAuthCore:
    def test_hash_and_verify(self):
        h = hash_password("hello123")
        assert h != "hello123"
        assert verify_password("hello123", h) is True
        assert verify_password("wrong", h) is False

    def test_create_and_decode_token(self):
        token = create_access_token({"sub": "1", "role": "admin"})
        payload = decode_access_token(token)
        assert payload["sub"] == "1"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        assert decode_access_token("not.a.token") is None


class TestLoginAPI:
    def test_login_success(self, client, admin):
        resp = client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "admin123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["role"] == "admin"
        assert data["expires_in"] > 0

    def test_login_wrong_password(self, client, admin):
        resp = client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "wrong"
        })
        assert resp.status_code == 401
        assert "错误" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "username": "nobody", "password": "x"
        })
        assert resp.status_code == 401

    def test_login_disabled_user(self, client, db, admin):
        admin.status = UserStatus.DISABLED
        db.commit()
        resp = client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "admin123"
        })
        assert resp.status_code == 403
        assert "禁用" in resp.json()["detail"]

    def test_init_admin_when_exists(self, client, admin):
        resp = client.post("/api/v1/auth/init")
        assert resp.status_code == 200
        assert resp.json()["message"] == "管理员已存在"

    def test_init_admin_first_time(self, client):
        resp = client.post("/api/v1/auth/init")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "管理员创建成功"
        assert data["username"] == "admin"

    def test_login_updates_last_login(self, client, admin, db):
        assert admin.last_login is None
        client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "admin123"
        })
        db.refresh(admin)
        assert admin.last_login is not None
