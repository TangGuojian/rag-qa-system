from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from app.db.mysql import Base
import enum


class KbStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(64), nullable=True)
    doc_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    graph_node_count = Column(Integer, default=0)
    graph_edge_count = Column(Integer, default=0)
    status = Column(SAEnum(KbStatus), nullable=False, default=KbStatus.ACTIVE)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
