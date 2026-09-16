import pytest
from unittest.mock import patch, MagicMock
from app.models.history import QaHistory


@pytest.fixture
def test_kb(client, admin_headers):
    resp = client.post("/api/v1/knowledge-bases", json={"name": "测试知识库"}, headers=admin_headers)
    return resp.json()


class TestQAAPI:
    @patch("app.api.qa.answer_question")
    def test_ask_question(self, mock_answer, client, admin_headers, test_kb):
        mock_answer.return_value = (
            "这是测试回答",
            [{"kb_name": "测试知识库", "filename": "test.txt", "content": "参考内容"}],
        )
        resp = client.post("/api/v1/qa/ask", json={
            "question": "测试问题",
            "kb_ids": [test_kb["id"]],
            "session_id": "session_test_1",
        }, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "这是测试回答"
        assert len(data["sources"]) == 1
        assert data["session_id"] == "session_test_1"

    @patch("app.api.qa.answer_question")
    def test_ask_question_records_history(self, mock_answer, client, admin_headers, test_kb, db):
        mock_answer.return_value = ("回答", [])
        client.post("/api/v1/qa/ask", json={
            "question": "问题1",
            "kb_ids": [test_kb["id"]],
            "session_id": "session_test_2",
        }, headers=admin_headers)

        history = db.query(QaHistory).filter(QaHistory.session_id == "session_test_2").first()
        assert history is not None
        assert history.question == "问题1"
        assert history.answer == "回答"

    @patch("app.api.qa.answer_question")
    def test_ask_question_engine_error(self, mock_answer, client, admin_headers, test_kb):
        mock_answer.side_effect = Exception("LLM API 错误")
        resp = client.post("/api/v1/qa/ask", json={
            "question": "问题",
            "kb_ids": [test_kb["id"]],
            "session_id": "session_err",
        }, headers=admin_headers)
        assert resp.status_code == 500
        assert "问答引擎错误" in resp.json()["detail"]

    def test_ask_question_no_auth(self, client, test_kb):
        resp = client.post("/api/v1/qa/ask", json={
            "question": "问题",
            "kb_ids": [test_kb["id"]],
        })
        assert resp.status_code in (401, 403)

    def test_submit_feedback(self, client, admin_headers, test_kb, db):
        record = QaHistory(
            user_id=1, session_id="fb_test", question="q",
            answer="a", kb_ids=[1]
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        resp = client.post("/api/v1/qa/feedback", json={
            "qa_id": record.id,
            "useful": True,
            "feedback": "很有用",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "反馈已记录"

        db.refresh(record)
        assert record.useful is True
        assert record.feedback == "很有用"

    def test_submit_feedback_not_found(self, client, admin_headers):
        resp = client.post("/api/v1/qa/feedback", json={
            "qa_id": 999,
            "useful": False,
        }, headers=admin_headers)
        assert resp.status_code == 404
