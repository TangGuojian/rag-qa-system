import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_chroma_collection():
    collection = MagicMock()
    collection.query.return_value = {
        "ids": [["id1", "id2"]],
        "documents": [["doc1 content", "doc2 content"]],
        "metadatas": [[{"kb_name": "test_kb", "filename": "test.txt", "kb_id": 1, "doc_id": 1},
                       {"kb_name": "test_kb", "filename": "test2.txt", "kb_id": 1, "doc_id": 2}]],
        "distances": [[0.1, 0.2]],
    }
    return collection


@pytest.fixture
def mock_neo4j_session():
    session = MagicMock()
    session.run.return_value = [
        MagicMock(
            doc_title="制度文件",
            doc_num="2026-001",
            agency_name="财务部",
            filename="test.pdf",
            content="文档内容",
        )
    ]
    return session


@pytest.fixture
def mock_llm_response():
    return MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="这是LLM生成的回答。")
            )
        ]
    )


@pytest.fixture
def mock_stream_chunks():
    return [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="这是"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="回答。"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
    ]
