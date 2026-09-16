import pytest
from app.models.user import User, UserRole, UserStatus


class TestUsersAPI:
    def test_list_users_admin(self, client, admin_headers, admin):
        resp = client.get("/api/v1/users", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        users = data.get("data") or data.get("users") or []
        assert len(users) >= 1
        usernames = [u["username"] for u in users]
        assert "admin" in usernames

    def test_list_users_non_admin_forbidden(self, client, user_headers, normal_user):
        resp = client.get("/api/v1/users", headers=user_headers)
        assert resp.status_code == 403

    def test_create_user(self, client, admin_headers, db):
        resp = client.post("/api/v1/users", json={
            "username": "newuser",
            "password": "pass123",
            "display_name": "New User",
            "role": "user",
        }, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data

        user = db.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.display_name == "New User"

    def test_create_duplicate_username(self, client, admin_headers, admin):
        resp = client.post("/api/v1/users", json={
            "username": "admin", "password": "x"
        }, headers=admin_headers)
        assert resp.status_code in (400, 409)
        assert "已存在" in resp.json()["detail"]

    def test_create_user_non_admin(self, client, user_headers):
        resp = client.post("/api/v1/users", json={
            "username": "hacker", "password": "x"
        }, headers=user_headers)
        assert resp.status_code == 403

    def test_update_user(self, client, admin_headers, db, normal_user):
        resp = client.put(f"/api/v1/users/{normal_user.id}", json={
            "display_name": "Updated Name",
            "role": "user",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated Name"

    def test_get_me(self, client, admin_token, admin_headers):
        resp = client.get("/api/v1/users/me", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert "api_key" in data

    def test_update_me(self, client, admin_headers):
        resp = client.put("/api/v1/users/me", json={
            "display_name": "MyNewName",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "MyNewName"

    def test_update_me_api_key(self, client, admin_headers, db):
        resp = client.put("/api/v1/users/me", json={
            "api_key": "sk-my-test-key-12345",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["api_key"] == "sk-my-test-key-12345"

    def test_get_me_no_auth(self, client):
        resp = client.get("/api/v1/users/me")
        assert resp.status_code in (401, 403)
