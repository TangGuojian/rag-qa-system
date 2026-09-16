import pytest
from unittest.mock import patch, MagicMock
from app.rag.llm import generate_answer, generate_answer_stream


class TestLLM:
    @patch("app.rag.llm.OpenAI")
    def test_generate_answer_with_contexts(self, mock_openai, mock_llm_response):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_openai.return_value = mock_client

        answer = generate_answer(
            question="差旅报销标准是多少？",
            contexts=[{"content": "差旅报销标准：一线城市300元/晚。", "filename": "报销制度.txt"}],
            api_key="sk-test",
        )
        assert answer == "这是LLM生成的回答。"
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.rag.llm.OpenAI")
    def test_generate_answer_without_api_key(self, mock_openai, mock_llm_response):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_openai.return_value = mock_client

        answer = generate_answer(
            question="测试",
            contexts=[],
            api_key="",
        )
        assert answer == "这是LLM生成的回答。"

    @patch("app.rag.llm.OpenAI")
    def test_generate_answer_with_user_key(self, mock_openai, mock_llm_response):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_openai.return_value = mock_client

        answer = generate_answer(
            question="测试",
            contexts=[],
            api_key="sk-user-custom-key",
        )
        assert answer == "这是LLM生成的回答。"

    @patch("app.rag.llm.OpenAI")
    def test_streaming_output(self, mock_openai, mock_stream_chunks):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = iter(mock_stream_chunks)
        mock_openai.return_value = mock_client

        tokens = list(generate_answer_stream(
            question="测试",
            contexts=[],
            api_key="sk-test",
        ))
        assert len(tokens) == 2
        assert tokens[0] == "这是"
        assert tokens[1] == "回答。"
