import pytest
from unittest.mock import patch, MagicMock
from app.rag.embedding import embed_text, embed_texts


class TestEmbedding:
    @patch("app.rag.embedding.OpenAI")
    def test_embed_text(self, mock_openai):
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=[0.1, 0.2, 0.3])]
        )
        mock_openai.return_value = mock_client

        result = embed_text("测试文本", api_key="sk-test")
        assert result == [0.1, 0.2, 0.3]

    @patch("app.rag.embedding.OpenAI")
    def test_embed_texts(self, mock_openai):
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = MagicMock(
            data=[
                MagicMock(embedding=[0.1, 0.2]),
                MagicMock(embedding=[0.3, 0.4]),
            ]
        )
        mock_openai.return_value = mock_client

        results = embed_texts(["文本1", "文本2"], api_key="sk-test")
        assert len(results) == 2
        assert results[0] == [0.1, 0.2]

    @patch("app.rag.embedding.OpenAI")
    def test_embed_text_empty(self, mock_openai):
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=[])]
        )
        mock_openai.return_value = mock_client

        result = embed_text("", api_key="sk-test")
        assert result == []
