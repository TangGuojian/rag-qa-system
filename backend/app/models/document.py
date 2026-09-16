from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.sql import func
from app.db.mysql import Base
import enum


class DocStatus(str, enum.Enum):
    PENDING = "pending"
    PARSING = "parsing"
    VECTORIZING = "vectorizing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    MD = "md"
    XLSX = "xlsx"
    TXT = "txt"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    filename = Column(String(256), nullable=False)
    filepath = Column(String(512), nullable=False)
    file_size = Column(BigInteger, default=0)
    file_type = Column(SAEnum(DocType), nullable=False)
    status = Column(SAEnum(DocStatus), nullable=False, default=DocStatus.PENDING, index=True)
    tags = Column(String(256), nullable=True, index=True)
    chunk_count = Column(Integer, default=0)
    error_msg = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
