import pytest
from app.models.config import SystemConfig


class TestConfigAPI:
    def test_get_config_default(self, client, admin_headers):
        resp = client.get("/api/v1/config", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["llm_model"] == "qwen3.7-plus"
        assert "temperature" in data
        assert "top_k" in data
        assert "threshold" in data

    def test_update_and_get_config(self, client, admin_headers, db):
        resp = client.put("/api/v1/config", json={
            "temperature": 0.8,
            "top_k": 5,
            "threshold": 0.5,
        }, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["config"]["temperature"] == 0.8

        row = db.query(SystemConfig).filter(SystemConfig.config_key == "app_config").first()
        assert row is not None
        assert row.config_value["temperature"] == 0.8

    def test_update_config_overwrite(self, client, admin_headers, db):
        client.put("/api/v1/config", json={"temperature": 0.5}, headers=admin_headers)
        client.put("/api/v1/config", json={"temperature": 1.0, "top_k": 10}, headers=admin_headers)

        row = db.query(SystemConfig).filter(SystemConfig.config_key == "app_config").first()
        assert row.config_value["temperature"] == 1.0
        assert row.config_value["top_k"] == 10

    def test_get_config_after_update(self, client, admin_headers):
        client.put("/api/v1/config", json={
            "chunk_size": 500,
        }, headers=admin_headers)

        resp = client.get("/api/v1/config", headers=admin_headers)
        data = resp.json()
        assert data["chunk_size"] == 500

    def test_update_config_non_admin(self, client, user_headers):
        resp = client.put("/api/v1/config", json={"temperature": 0.5}, headers=user_headers)
        assert resp.status_code == 403
