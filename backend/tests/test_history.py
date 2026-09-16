import pytest
from app.models.history import QaHistory


def create_history(db, user_id, session_id, question, answer=None):
    record = QaHistory(
        user_id=user_id, session_id=session_id,
        question=question, answer=answer or f"回答：{question}",
        kb_ids=[1],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


class TestHistoryAPI:
    def test_list_history(self, client, admin_headers, db, admin):
        create_history(db, admin.id, "s1", "问题1")
        create_history(db, admin.id, "s1", "问题2")

        resp = client.get("/api/v1/history", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert len(data["data"]) == 2

    def test_list_history_pagination(self, client, admin_headers, db, admin):
        for i in range(5):
            create_history(db, admin.id, f"s{i}", f"问题{i}")

        resp = client.get("/api/v1/history?page=1&size=2", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2

    def test_list_history_filter_by_session(self, client, admin_headers, db, admin):
        create_history(db, admin.id, "session_a", "A1")
        create_history(db, admin.id, "session_a", "A2")
        create_history(db, admin.id, "session_b", "B1")

        resp = client.get("/api/v1/history?session_id=session_a", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2
        assert all(r["session_id"] == "session_a" for r in data["data"])

    def test_list_history_filter_by_keyword(self, client, admin_headers, db, admin):
        create_history(db, admin.id, "s1", "差旅报销流程")
        create_history(db, admin.id, "s2", "财务审批规定")
        create_history(db, admin.id, "s3", "员工考勤制度")

        resp = client.get("/api/v1/history?keyword=报销", headers=admin_headers)
        data = resp.json()
        assert "data" in data
        assert len(data["data"]) >= 1

        resp = client.get("/api/v1/history?keyword=制度", headers=admin_headers)
        data = resp.json()
        assert len(data["data"]) >= 1

    def test_list_history_date_range(self, client, admin_headers, db, admin):
        create_history(db, admin.id, "s1", "问题1")

        from datetime import datetime
        today = datetime.utcnow().strftime("%Y-%m-%d")
        resp = client.get(f"/api/v1/history?start_date={today}&end_date={today}", headers=admin_headers)
        assert len(resp.json()["data"]) == 1

    def test_delete_history(self, client, admin_headers, db, admin):
        record = create_history(db, admin.id, "s_del", "待删除")
        qa_id = record.id

        resp = client.delete(f"/api/v1/history/{qa_id}", headers=admin_headers)
        assert resp.status_code in (200, 204)

        assert db.query(QaHistory).filter(QaHistory.id == qa_id).first() is None

    def test_delete_history_not_found(self, client, admin_headers):
        resp = client.delete("/api/v1/history/999", headers=admin_headers)
        assert resp.status_code == 404
