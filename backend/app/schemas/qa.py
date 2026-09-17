from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AskRequest(BaseModel):
    question: str
    kb_ids: List[int]
    # 多轮会话标识。不传时由服务端生成，便于直接调试接口（如 /docs 里试调用）
    session_id: Optional[str] = None


class SourceInfo(BaseModel):
    kb_name: str
    filename: str
    content: str


class QAResult(BaseModel):
    answer: str
    sources: List[SourceInfo] = []
    session_id: str


class FeedbackRequest(BaseModel):
    qa_id: int
    useful: bool
    feedback: Optional[str] = None


class QAResponse(BaseModel):
    id: int
    question: str
    answer: Optional[str] = None
    useful: Optional[bool] = None
    kb_ids: list
    created_at: datetime

    model_config = {"from_attributes": True}
