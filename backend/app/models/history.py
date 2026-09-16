from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.mysql import Base


class QaHistory(Base):
    __tablename__ = "qa_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    kb_ids = Column(JSON, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    sources = Column(JSON, nullable=True)
    useful = Column(Boolean, nullable=True)
    feedback = Column(Text, nullable=True)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now(), index=True)
