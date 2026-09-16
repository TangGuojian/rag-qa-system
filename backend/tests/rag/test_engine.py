import pytest
from unittest.mock import patch, MagicMock


class TestRagEngine:
    @patch("app.rag.engine._load_rag_config")
    @patch("app.rag.engine._load_history")
    @patch("app.rag.engine._search_contexts")
    @patch("app.rag.engine.generate_answer")
    def test_answer_question_success(
        self, mock_generate, mock_search, mock_history, mock_config
    ):
        from app.rag.engine import answer_question

        mock_config.return_value = {"temperature": 0.7, "top_k": 3, "threshold": 0.5,
                                     "chat_temperature": 0.7, "chat_max_tokens": 2048,
                                     "max_tokens": 2048}
        mock_history.return_value = []
        mock_search.return_value = [
            {"content": "参考内容", "kb_name": "KB1", "filename": "doc1.txt", "score": 0.9}
        ]
        mock_generate.return_value = "LLM回答"

        answer, sources = answer_question(
            "测试问题", [1], None,
            session_id="s1", db_session=MagicMock(), user_id=1,
        )
        assert answer == "LLM回答"
        assert len(sources) == 1
        assert sources[0]["kb_name"] == "KB1"

    @patch("app.rag.engine._load_rag_config")
    @patch("app.rag.engine._load_history")
    @patch("app.rag.engine._search_contexts")
    def test_answer_question_no_context(
        self, mock_search, mock_history, mock_config
    ):
        from app.rag.engine import answer_question

        mock_config.return_value = {"temperature": 0.7, "top_k": 3, "threshold": 0.5,
                                     "chat_temperature": 0.7, "chat_max_tokens": 2048,
                                     "max_tokens": 2048}
        mock_history.return_value = []
        mock_search.return_value = []

        answer, sources = answer_question(
            "测试", [1], None,
            session_id="s1", db_session=MagicMock(), user_id=1,
        )
        assert "未在知识库中找到相关信息" in answer
        assert sources == []

    @patch("app.rag.engine._load_rag_config")
    @patch("app.rag.engine._load_history")
    @patch("app.rag.engine._search_contexts")
    def test_answer_question_stream_no_context(
        self, mock_search, mock_history, mock_config
    ):
        from app.rag.engine import answer_question_stream

        mock_config.return_value = {"temperature": 0.7, "top_k": 3, "threshold": 0.5,
                                     "chat_temperature": 0.7, "chat_max_tokens": 2048,
                                     "max_tokens": 2048}
        mock_history.return_value = []
        mock_search.return_value = []

        tokens = list(answer_question_stream(
            "测试", [1], None,
            session_id="s1", db_session=MagicMock(), user_id=1,
        ))
        assert "未在知识库中找到相关信息" in "".join(tokens)

    @patch("app.rag.engine._load_rag_config")
    @patch("app.rag.engine._load_history")
    @patch("app.rag.engine._search_contexts")
    @patch("app.rag.engine.generate_answer_stream")
    def test_answer_question_stream_with_context(
        self, mock_stream, mock_search, mock_history, mock_config
    ):
        from app.rag.engine import answer_question_stream

        mock_config.return_value = {"temperature": 0.7, "top_k": 3, "threshold": 0.5,
                                     "chat_temperature": 0.7, "chat_max_tokens": 2048,
                                     "max_tokens": 2048}
        mock_history.return_value = []
        mock_search.return_value = [{"content": "c1", "kb_name": "KB1", "filename": "f1.txt", "score": 0.9}]
        mock_stream.return_value = iter(["tok1", "tok2"])

        tokens = list(answer_question_stream(
            "测试", [1], None,
            session_id="s1", db_session=MagicMock(), user_id=1,
        ))
        assert "".join(tokens) == "tok1tok2"

    @patch("app.rag.engine.SessionLocal")
    def test_load_rag_config_default(self, mock_db):
        mock_db.return_value.query.return_value.filter.return_value.first.return_value = None
        from app.rag.engine import _load_rag_config
        cfg = _load_rag_config()
        assert "temperature" in cfg
        assert "top_k" in cfg
        assert "threshold" in cfg
        assert "max_tokens" in cfg

    @patch("app.rag.engine._load_rag_config")
    def test_answer_question_empty_kb_ids(self, mock_config):
        from app.rag.engine import answer_question

        mock_config.return_value = {"temperature": 0.7, "top_k": 3, "threshold": 0.5,
                                     "chat_temperature": 0.7, "chat_max_tokens": 2048,
                                     "max_tokens": 2048}

        with patch("app.rag.engine._load_history", return_value=[]):
            with patch("app.rag.engine._search_contexts", return_value=[]):
                answer, sources = answer_question(
                    "测试", [], None
                )
                assert "未在知识库中找到相关信息" in answer
                assert sources == []
