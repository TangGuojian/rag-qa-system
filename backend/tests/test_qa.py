import json
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
        # 引擎异常会被 humanize_error 翻译成可读提示，并保留原始错误信息
        assert "调用失败" in resp.json()["detail"]
        assert "LLM API 错误" in resp.json()["detail"]

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

    @patch("app.db.mysql.SessionLocal")
    @patch("app.api.qa.answer_question_stream")
    def test_ask_stream_returns_sources_and_qa_id(self, mock_stream, mock_session_local, client, db, admin_headers, test_kb):
        """流式回答的结束事件必须带上溯源与 qa_id。

        回归用例：曾因 db.close() 之后再访问 record.id 抛 DetachedInstanceError，
        导致 done 事件发不出去——界面上没有溯源、反馈按钮也静默失效。

        注意：流式接口不走 get_db 依赖注入，而是自己用 SessionLocal() 取会话，
        因此这里把 SessionLocal 指向测试会话，让它在同一个事务里读到 admin。
        """
        mock_session_local.return_value = db

        def gen(*args, **kwargs):
            yield "你好"
            yield "世界"
            yield {"sources": [
                {"kb_name": "测试知识库", "filename": "test.txt", "content": "参考内容"}
            ]}

        mock_stream.side_effect = gen
        resp = client.post("/api/v1/qa/ask/stream", json={
            "question": "流式问题",
            "kb_ids": [test_kb["id"]],
            "session_id": "session_stream_1",
        }, headers=admin_headers)
        assert resp.status_code == 200

        tokens, done_events = [], []
        for line in resp.text.split("\n"):
            if line.startswith("data: "):
                payload = json.loads(line[6:])
                (done_events if payload.get("done") else tokens).append(payload)

        assert "".join(t["token"] for t in tokens) == "你好世界"
        assert len(done_events) == 1
        assert not done_events[0].get("error")
        assert len(done_events[0]["sources"]) == 1
        # qa_id 必须存在，否则前端的「有帮助 / 没帮助」反馈无处可写
        assert done_events[0]["qa_id"]
