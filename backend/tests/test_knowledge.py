import pytest
from app.models.kb import KnowledgeBase, KbStatus


class TestKnowledgeBaseAPI:
    def test_list_kbs_empty(self, client, admin_headers):
        resp = client.get("/api/v1/knowledge-bases", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_kb(self, client, admin_headers):
        resp = client.post("/api/v1/knowledge-bases", json={
            "name": "测试知识库",
            "description": "测试描述"
        }, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "测试知识库"
        assert data["description"] == "测试描述"
        assert "id" in data

    def test_create_kb_duplicate_name(self, client, admin_headers, db):
        client.post("/api/v1/knowledge-bases", json={"name": "测试知识库"}, headers=admin_headers)
        resp = client.post("/api/v1/knowledge-bases", json={"name": "测试知识库"}, headers=admin_headers)
        assert resp.status_code == 409
        assert "已存在" in resp.json()["detail"]

    def test_create_kb_non_admin(self, client, user_headers):
        resp = client.post("/api/v1/knowledge-bases", json={
            "name": "测试知识库"
        }, headers=user_headers)
        assert resp.status_code == 403
        assert "管理员" in resp.json()["detail"]

    def test_update_kb(self, client, admin_headers, db):
        create_resp = client.post("/api/v1/knowledge-bases", json={
            "name": "旧名称", "description": "旧描述"
        }, headers=admin_headers)
        kb_id = create_resp.json()["id"]

        resp = client.put(f"/api/v1/knowledge-bases/{kb_id}", json={
            "name": "新名称", "description": "新描述"
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "新名称"
        assert resp.json()["description"] == "新描述"

    def test_update_kb_not_found(self, client, admin_headers):
        resp = client.put("/api/v1/knowledge-bases/999", json={
            "name": "不存在"
        }, headers=admin_headers)
        assert resp.status_code == 404

    def test_delete_kb(self, client, admin_headers, db):
        create_resp = client.post("/api/v1/knowledge-bases", json={"name": "待删除"}, headers=admin_headers)
        kb_id = create_resp.json()["id"]

        resp = client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=admin_headers)
        assert resp.status_code == 204

        db_kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        assert db_kb.status == KbStatus.ARCHIVED

    def test_delete_kb_not_found(self, client, admin_headers):
        resp = client.delete("/api/v1/knowledge-bases/999", headers=admin_headers)
        assert resp.status_code == 404

    def test_list_kbs_with_search(self, client, admin_headers, db):
        client.post("/api/v1/knowledge-bases", json={"name": "财务制度"}, headers=admin_headers)
        client.post("/api/v1/knowledge-bases", json={"name": "人事制度"}, headers=admin_headers)

        resp = client.get("/api/v1/knowledge-bases?search=财务", headers=admin_headers)
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "财务制度"

    def test_non_admin_can_list(self, client, user_headers, db):
        client.post("/api/v1/knowledge-bases", json={"name": "公共知识库"}, headers=user_headers)
        resp = client.get("/api/v1/knowledge-bases", headers=user_headers)
        assert resp.status_code == 200
