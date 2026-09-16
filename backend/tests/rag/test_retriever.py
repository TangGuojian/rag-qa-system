import pytest
from unittest.mock import patch, MagicMock
from app.rag.retriever import search_knowledge


class TestRetriever:
    @patch("app.rag.retriever.get_collection")
    @patch("app.rag.retriever.embed_text")
    def test_retrieve_with_results(self, mock_embed, mock_get_col, mock_chroma_collection):
        mock_embed.return_value = [0.1] * 1024
        mock_get_col.return_value = mock_chroma_collection
        results = search_knowledge(
            question="差旅报销标准",
            kb_ids=[1],
            top_k=3,
            threshold=0.3,
        )
        assert len(results) == 2
        assert results[0].content == "doc1 content"
        assert results[0].kb_name == "test_kb"

    @patch("app.rag.retriever.get_collection")
    @patch("app.rag.retriever.embed_text")
    def test_retrieve_empty_results(self, mock_embed, mock_get_col):
        mock_embed.return_value = [0.1] * 1024
        empty_collection = MagicMock()
        empty_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        mock_get_col.return_value = empty_collection
        results = search_knowledge(
            question="不存在的文档",
            kb_ids=[999],
            top_k=3,
            threshold=0.5,
        )
        assert results == []

    @patch("app.rag.retriever.get_collection")
    @patch("app.rag.retriever.embed_text")
    def test_retrieve_respects_threshold(self, mock_embed, mock_get_col):
        mock_embed.return_value = [0.1] * 1024
        collection = MagicMock()
        collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"filename": "a.txt", "kb_id": 1, "kb_name": "KB", "doc_id": 1},
                           {"filename": "b.txt", "kb_id": 1, "kb_name": "KB", "doc_id": 2}]],
            "distances": [[0.1, 0.8]],
        }
        mock_get_col.return_value = collection
        results = search_knowledge(
            question="测试",
            kb_ids=[1],
            top_k=3,
            threshold=0.3,
        )
        assert len(results) == 1
        assert results[0].content == "doc1"
