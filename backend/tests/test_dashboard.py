import pytest
from app.models.history import QaHistory
from app.models.kb import KnowledgeBase
from app.models.document import Document, DocStatus, DocType


class TestDashboardAPI:
    def test_kb_overview_empty(self, client, admin_headers):
        resp = client.get("/api/v1/dashboard/kb-overview", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_kb_overview_with_data(self, client, admin_headers, db):
        kb = KnowledgeBase(name="测试KB", description="desc")
        db.add(kb)
        db.commit()
        db.refresh(kb)

        doc = Document(
            kb_id=kb.id, filename="test.txt",
            filepath="/tmp/test.txt", file_size=100,
            file_type=DocType.TXT, status=DocStatus.COMPLETED,
            uploaded_by=1, chunk_count=5,
        )
        db.add(doc)
        db.commit()

        resp = client.get("/api/v1/dashboard/kb-overview", headers=admin_headers)
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "测试KB"
        assert data[0]["doc_count"] == 1
        assert data[0]["parsed"] == 1

    def test_qa_stats_empty(self, client, admin_headers):
        resp = client.get("/api/v1/dashboard/qa-stats", headers=admin_headers)
        data = resp.json()
        assert data["total_qa"] == 0
        assert data["active_users"] == 0
        assert len(data["trend"]) == 7

    def test_qa_stats_with_data(self, client, admin_headers, db):
        record = QaHistory(
            user_id=1, session_id="s1", question="q",
            answer="a", kb_ids=[1],
        )
        db.add(record)
        db.commit()

        resp = client.get("/api/v1/dashboard/qa-stats", headers=admin_headers)
        data = resp.json()
        assert data["total_qa"] == 1

    def test_system_status(self, client, admin_headers):
        resp = client.get("/api/v1/dashboard/system-status", headers=admin_headers)
        data = resp.json()
        assert "storage_used" in data
        assert "api_calls_today" in data

    def test_system_status_with_data(self, client, admin_headers, db):
        doc = Document(
            kb_id=1, filename="test.txt",
            filepath="/tmp/test.txt", file_size=1024,
            file_type=DocType.TXT, status=DocStatus.PENDING,
            uploaded_by=1,
        )
        db.add(doc)
        db.commit()

        resp = client.get("/api/v1/dashboard/system-status", headers=admin_headers)
        data = resp.json()
        assert data["storage_used"] >= 1024

    def test_hot_topics_empty(self, client, admin_headers):
        resp = client.get("/api/v1/dashboard/hot-topics", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_hot_topics_with_data(self, client, admin_headers, db):
        questions = [
            "差旅报销流程是什么",
            "差旅报销需要哪些材料",
            "差旅报销标准是多少",
            "预算编制方法有哪些",
            "预算审批流程",
        ]
        for i, q in enumerate(questions):
            record = QaHistory(
                user_id=1, session_id=f"s{i}",
                question=q, answer="", kb_ids=[1],
            )
            db.add(record)
        db.commit()

        resp = client.get("/api/v1/dashboard/hot-topics", headers=admin_headers)
        data = resp.json()
        assert len(data) > 0
        assert any("差旅" in item["name"] for item in data)

    def test_dashboard_non_admin(self, client, user_headers):
        for path in ["/api/v1/dashboard/kb-overview", "/api/v1/dashboard/qa-stats",
                     "/api/v1/dashboard/system-status", "/api/v1/dashboard/hot-topics"]:
            resp = client.get(path, headers=user_headers)
            assert resp.status_code == 403, f"{path} should require admin"
